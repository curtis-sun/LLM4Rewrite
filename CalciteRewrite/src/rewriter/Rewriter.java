package rewriter;

import com.google.common.collect.ImmutableSet;
import org.apache.calcite.plan.RelOptRule;
import org.apache.calcite.plan.hep.HepMatchOrder;
import org.apache.calcite.plan.hep.HepPlanner;
import org.apache.calcite.plan.hep.HepProgramBuilder;
import org.apache.calcite.rel.RelNode;
import org.apache.calcite.rel.RelVisitor;
import org.apache.calcite.rel.core.RelFactories;
import org.apache.calcite.rel.logical.LogicalFilter;
import org.apache.calcite.rel.rel2sql.RelToSqlConverter;
import org.apache.calcite.rel.rules.CoreRules;
import org.apache.calcite.sql.pretty.SqlPrettyWriter;
import org.apache.calcite.sql2rel.RelDecorrelator;
import org.apache.calcite.test.RelOptFixture;
import org.apache.calcite.tools.RelBuilder;
import org.apache.calcite.util.Util;
import org.checkerframework.checker.nullness.qual.Nullable;

import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import static rewriter.MyRules.*;
import static rewriter.SqlIo.*;

public class Rewriter {
    public static String explain(RelNode rel) {
        return rel.explain().replace("LogicalTableScan(table=[[CATALOG, SALES, ", "LogicalTableScan(table=[[");
    }

    private static boolean isFilterWithVariables(RelNode node) {
        return node instanceof LogicalFilter && !node.getVariablesSet().isEmpty();
    }

    public static boolean containsFilterWithVariables(RelNode ancestor) {
        if (isFilterWithVariables(ancestor)) {
            // Short-cut common case.
            return true;
        }
        try {
            new RelVisitor() {
                @Override public void visit(RelNode node, int ordinal,
                                            @Nullable RelNode parent) {
                    if (isFilterWithVariables(node)) {
                        throw Util.FoundOne.NULL;
                    }
                    super.visit(node, ordinal, parent);
                }
                // CHECKSTYLE: IGNORE 1
            }.go(ancestor);
            return false;
        } catch (Util.FoundOne e) {
            return true;
        }
    }

    private static List<Map<String, String>> matchRules(String sql, List<String> createTables, Map<String, RelOptRule> ruleSet, String database, boolean verbose) {
        RelOptFixture fixture = inputSql(sql, createTables, database);
        List<Map<String, String>> matchRules = new ArrayList<>();
        try {
            RelNode relBefore = fixture.toRel();
            for (Map.Entry<String, RelOptRule> entry: ruleSet.entrySet()){
                final String ruleName = entry.getKey();
                final RelOptRule rule = entry.getValue();
                try {
                    HepProgramBuilder builder = new HepProgramBuilder();
                    builder.addRuleInstance(rule);
                    HepPlanner hepPlanner = new HepPlanner(builder.addMatchOrder(HepMatchOrder.TOP_DOWN).build());
                    RelNode relAfter;
                    if (SEMI_JOIN_RULES.containsKey(ruleName)) {
                        relAfter = fixture
                                .withPreRule(
                                        CoreRules.PROJECT_TO_SEMI_JOIN,
                                        CoreRules.JOIN_ON_UNIQUE_TO_SEMI_JOIN,
                                        CoreRules.JOIN_TO_SEMI_JOIN
                                )
                                .withPlanner(hepPlanner)
                                .findBest(relBefore);
                    } else {
                        relAfter = fixture
                                .withPlanner(hepPlanner)
                                .findBest(relBefore);
                    }
                    final String planBefore = explain(relBefore);
                    final String planAfter= explain(relAfter);
                    if (! planAfter.equals(planBefore)) {
                        Map matchRule = new HashMap();
                        matchRule.put("name", ruleName);
                        matchRule.put("plan_before", planBefore);
                        matchRule.put("plan_after", planAfter);
                        String sqlAfter = outputSql(
                                (new SqlPrettyWriter()).format(
                                        (new RelToSqlConverter(getProduct(database).getDialect())).visitRoot(relAfter).asStatement()));
                        matchRule.put("sql_after", sqlAfter);
                        matchRules.add(matchRule);
                    }
                } catch(Exception e) {
                    if (verbose) {
                        System.out.println("Failed to match rule: " + ruleName);
                        e.printStackTrace();
                    }
                }
            }
        } catch(Exception e) {
            e.printStackTrace();
        }
        return matchRules;
    }

    public static List<Map<String, String>> matchExploreRules(String sql, List<String> createTables, String database, boolean verbose) {
        return matchRules(sql, createTables, EXPLORE_RULES, database, verbose);
    }

    public static List<Map<String, String>> matchNormalRules(String sql, List<String> createTables, String database, boolean verbose) {
        return matchRules(sql, createTables, NORMAL_RULES, database, verbose);
    }

    public static List<Map<String, String>> matchAllRules(String sql, List<String> createTables, String database, boolean verbose) {
        List<Map<String, String>> normalRules = matchNormalRules(sql, createTables, database, verbose);
        normalRules.forEach(r -> {
            r.put("type", "normal");
        });
        List<Map<String, String>> exploreRules = matchExploreRules(sql, createTables, database, verbose);
        exploreRules.forEach(r -> {
            r.put("type", "explore");
        });
        return Stream.concat(normalRules.stream(), exploreRules.stream()).collect(Collectors.toList());
    }

    private static void _rewrite(RewriteResult res, List<String> ruleNames, int rounds, RelOptFixture fixture) {
        for  (int i = 0; i < rounds; i ++) {
            for (String ruleName: ruleNames) {
                try {
                    final RelOptRule rule = USED_RULES.get(ruleName);
                    final RelNode relBefore = res.r2;
                    HepProgramBuilder builder = new HepProgramBuilder();
                    builder.addRuleInstance(rule);
                    HepPlanner hepPlanner = new HepPlanner(builder.addMatchOrder(HepMatchOrder.TOP_DOWN).build());
                    boolean lateDecorrelate = ImmutableSet.of(
                                    CoreRules.JOIN_SUB_QUERY_TO_CORRELATE,
                                    CoreRules.PROJECT_SUB_QUERY_TO_CORRELATE,
                                    CoreRules.FILTER_SUB_QUERY_TO_CORRELATE,
                                    CoreRules.JOIN_TO_CORRELATE)
                            .contains(rule);
                    RelNode relAfter = fixture
                            .withPlanner(hepPlanner)
                            .findBest(relBefore);
                    boolean flag = true;
                    if (lateDecorrelate && !containsFilterWithVariables(relAfter)) {
                        final RelBuilder relBuilder =
                                RelFactories.LOGICAL_BUILDER.create(relBefore.getCluster(), null);
                        final RelNode r1 = RelDecorrelator.decorrelateQuery(relAfter, relBuilder);
                        flag = rule != CoreRules.JOIN_TO_CORRELATE || !explain(r1).equals(explain(relAfter));
                        relAfter = r1;
                    }
                    final String planBefore = explain(relBefore);
                    final String planAfter= explain(relAfter);
                    if (!planAfter.equals(planBefore) && flag) {
                        res.rules.add(ruleName);
                        res.r2 = relAfter;
                    }
                } catch (Exception ignored) {}
            }
        }
    }

    public static List<RewriteResult> traverseRewrite(String sql, List<String> createTables, List<String> ruleNames, int rounds, String database) {
        long startTime = System.currentTimeMillis();
        RelOptFixture fixture = inputSql(sql, createTables, database);
        List<List<RewriteResult>> midResultsDP = new ArrayList<>();
        try {
            final RelNode r1 = fixture.toRel();
            RelNode r2 = r1;
            try {
                r2 = fixture
                        .withRule(
                                CoreRules.PROJECT_TO_SEMI_JOIN,
                                CoreRules.JOIN_ON_UNIQUE_TO_SEMI_JOIN,
                                CoreRules.JOIN_TO_SEMI_JOIN
                        )
                        .findBest(r1);
            } catch (Exception ignored) {}
            List<RewriteResult> iniResults = new ArrayList<>();
            for (String rule: ruleNames) {
                RewriteResult midRes = new RewriteResult();
                midRes.r1 = r1;
                midRes.r2 = r2;
                _rewrite(midRes, List.of(rule), rounds, fixture);
                if (midRes.rules.size() == 1) {
                    iniResults.add(midRes);
                }
            }
            midResultsDP.add(iniResults);
            for (int i = 2; i <= ruleNames.size(); i ++) {
                List<RewriteResult> curResults = new ArrayList<>();
                for (RewriteResult pre: midResultsDP.get(i - 2)) {
                    for (String rule: ruleNames) {
                        if (pre.rules.contains(rule)) {
                            continue;
                        }
                        RewriteResult midRes = new RewriteResult();
                        midRes.r1 = pre.r1;
                        midRes.r2 = pre.r2;
                        midRes.rules = new ArrayList<>(pre.rules);
                        _rewrite(midRes, List.of(rule), rounds, fixture);
                        if (midRes.rules.size() == i) {
                            curResults.add(midRes);
                        }
                    }
                }
                midResultsDP.add(curResults);
            }

            List<RewriteResult> midResults = midResultsDP.stream().flatMap(List::stream).toList();
            for (RewriteResult midRes: midResults) {
                midRes.r3 = midRes.r2;
                for (int i = 0; i < rounds; i ++) {
                    try {
                        HepProgramBuilder builder = new HepProgramBuilder();
                        PRUNE_EMPTY_RULES.forEach(builder::addRuleInstance);
                        HepPlanner hepPlanner = new HepPlanner(builder.addMatchOrder(HepMatchOrder.TOP_DOWN).build());
                        midRes.r3 = fixture
                                .withPlanner(hepPlanner)
                                .findBest(midRes.r3);
                    } catch (Exception ignored) {
                        break;
                    }
                }

                try {
                    midRes.sql = outputSql(
                            (new SqlPrettyWriter()).format(
                                    (new RelToSqlConverter(getProduct(database).getDialect())).visitRoot(midRes.r3).asStatement()
                            )
                    );
                } catch (Exception e) {
                    // e.printStackTrace();
                }
            }

            long time = System.currentTimeMillis() - startTime;
            midResults.forEach(r -> {
                r.time = time;
            });
            return midResults;
        } catch(Exception e) {
            // e.printStackTrace();
        }
        return Collections.emptyList();
    }

    public static RewriteResult rewrite(String sql, List<String> createTables, List<String> ruleNames, int rounds, String database) {
        long startTime = System.currentTimeMillis();
        RelOptFixture fixture = inputSql(sql, createTables, database);
        RewriteResult res = new RewriteResult();
        try {
            res.r1 = fixture.toRel();
            res.r2 = res.r1;
            try {
                res.r2 = fixture
                        .withRule(
                                CoreRules.PROJECT_TO_SEMI_JOIN,
                                CoreRules.JOIN_ON_UNIQUE_TO_SEMI_JOIN,
                                CoreRules.JOIN_TO_SEMI_JOIN
                        )
                        .findBest(res.r2);
            } catch (Exception ignored) {}
            _rewrite(res, ruleNames, rounds, fixture);

            res.r3 = res.r2;
            for (int i = 0; i < rounds; i ++) {
                try {
                    HepProgramBuilder builder = new HepProgramBuilder();
                    PRUNE_EMPTY_RULES.forEach(builder::addRuleInstance);
                    HepPlanner hepPlanner = new HepPlanner(builder.addMatchOrder(HepMatchOrder.TOP_DOWN).build());
                    res.r3 = fixture
                            .withPlanner(hepPlanner)
                            .findBest(res.r3);
                } catch (Exception ignored) {
                    break;
                }
            }

            try {
                res.sql = outputSql(
                        (new SqlPrettyWriter()).format(
                                (new RelToSqlConverter(getProduct(database).getDialect())).visitRoot(res.r3).asStatement()
                        )
                );
            } catch (NullPointerException e) {
                if ((e.getMessage().contains("rightResult.neededAlias is null, node is")
                        || e.getMessage().matches("variable .*? is not found"))
                        && ruleNames.contains("JOIN_TO_CORRELATE")) {
                    List<String> debugRuleNames = new ArrayList<>(ruleNames);
                    debugRuleNames.remove("JOIN_TO_CORRELATE");
                    res = rewrite(sql, createTables, debugRuleNames, rounds, database);
                } else {
                     e.printStackTrace();
                }
            } catch (Exception e) {
                 e.printStackTrace();
            }
        } catch(Exception e) {
            e.printStackTrace();
        }
        res.time = System.currentTimeMillis() - startTime;
        return res;
    }
}
