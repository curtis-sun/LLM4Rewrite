package rewriter;

import org.apache.calcite.plan.RelOptRule;
import org.apache.calcite.rel.core.Filter;
import org.apache.calcite.rel.core.Join;
import org.apache.calcite.rel.logical.LogicalFilter;
import org.apache.calcite.rel.logical.LogicalProject;
import org.apache.calcite.rel.rules.CoreRules;
import org.apache.calcite.rel.rules.FilterJoinRule;
import org.apache.calcite.rel.rules.FilterProjectTransposeRule;
import org.apache.calcite.rel.rules.ProjectFilterTransposeRule;
import org.apache.calcite.rel.rules.PruneEmptyRules;
import org.apache.calcite.rex.RexUtil;
import rules.MyReduceExpressionsRule;

import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import static java.util.Map.entry;

public class MyRules {
    public static final MyReduceExpressionsRule.MyFilterReduceExpressionsRule FILTER_REDUCE_EXPRESSIONS =
            MyReduceExpressionsRule.MyFilterReduceExpressionsRule.MyFilterReduceExpressionsRuleConfig.DEFAULT
                    .withOperandSupplier(
                            b -> b.operand(Filter.class).predicate(f -> f.getVariablesSet().isEmpty()).anyInputs())
                    .as(MyReduceExpressionsRule.MyFilterReduceExpressionsRule.MyFilterReduceExpressionsRuleConfig.class)
                    .toRule();

    public static final MyReduceExpressionsRule.MyJoinReduceExpressionsRule JOIN_REDUCE_EXPRESSIONS =
            MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig.DEFAULT.toRule();

    public static final MyReduceExpressionsRule.MyProjectReduceExpressionsRule PROJECT_REDUCE_EXPRESSIONS =
            MyReduceExpressionsRule.MyProjectReduceExpressionsRule.MyProjectReduceExpressionsRuleConfig.DEFAULT.toRule();
    public static final MyReduceExpressionsRule.MyWindowReduceExpressionsRule WINDOW_REDUCE_EXPRESSIONS =
            MyReduceExpressionsRule.MyWindowReduceExpressionsRule.MyWindowReduceExpressionsRuleConfig.DEFAULT.toRule();

    public static final FilterJoinRule.FilterIntoJoinRule FILTER_INTO_JOIN =
            FilterJoinRule.FilterIntoJoinRule.FilterIntoJoinRuleConfig.DEFAULT.withOperandSupplier(b0 ->
                            b0.operand(Filter.class).predicate(f -> f.getVariablesSet().isEmpty()).oneInput(b1 ->
                                    b1.operand(Join.class).anyInputs()))
                    .as(FilterJoinRule.FilterIntoJoinRule.FilterIntoJoinRuleConfig.class).toRule();

    public static final ProjectFilterTransposeRule PROJECT_FILTER_TRANSPOSE =
            ProjectFilterTransposeRule.Config.DEFAULT.withOperandSupplier(b0 ->
                            b0.operand(LogicalProject.class).oneInput(b1 ->
                                    b1.operand(LogicalFilter.class)
                                            .predicate(f -> f.getVariablesSet().isEmpty()).anyInputs()))
                    .as(ProjectFilterTransposeRule.Config.class)
                    .toRule();
    public static final FilterProjectTransposeRule FILTER_PROJECT_TRANSPOSE =
            FilterProjectTransposeRule.Config.DEFAULT.withOperandSupplier(b0 ->
                            b0.operand(LogicalFilter.class).predicate(f -> !RexUtil.containsCorrelation(f.getCondition()) && f.getVariablesSet().isEmpty())
                    .oneInput(b1 -> b1.operand(LogicalProject.class).anyInputs()))
                    .as(FilterProjectTransposeRule.Config.class)
                    .toRule();

    public static final Map<String, RelOptRule> NORMAL_RULES = Map.ofEntries(
            entry("AGGREGATE_ANY_PULL_UP_CONSTANTS", CoreRules.AGGREGATE_ANY_PULL_UP_CONSTANTS),
            entry("AGGREGATE_CASE_TO_FILTER", CoreRules.AGGREGATE_CASE_TO_FILTER),
            entry("AGGREGATE_MERGE", CoreRules.AGGREGATE_MERGE),
            entry("AGGREGATE_PROJECT_MERGE", CoreRules.AGGREGATE_PROJECT_MERGE),
            entry("AGGREGATE_REMOVE", CoreRules.AGGREGATE_REMOVE),
            entry("AGGREGATE_JOIN_JOIN_REMOVE", CoreRules.AGGREGATE_JOIN_JOIN_REMOVE),
            entry("AGGREGATE_JOIN_REMOVE", CoreRules.AGGREGATE_JOIN_REMOVE),
            entry("FILTER_AGGREGATE_TRANSPOSE", CoreRules.FILTER_AGGREGATE_TRANSPOSE),
            entry("FILTER_CORRELATE", CoreRules.FILTER_CORRELATE),
            entry("FILTER_EXPAND_IS_NOT_DISTINCT_FROM", CoreRules.FILTER_EXPAND_IS_NOT_DISTINCT_FROM),
            entry("FILTER_INTO_JOIN", FILTER_INTO_JOIN),
            entry("FILTER_MERGE", CoreRules.FILTER_MERGE),
            entry("FILTER_PROJECT_TRANSPOSE", FILTER_PROJECT_TRANSPOSE),
            entry("FILTER_REDUCE_EXPRESSIONS", MyRules.FILTER_REDUCE_EXPRESSIONS),
            entry("FILTER_SET_OP_TRANSPOSE", CoreRules.FILTER_SET_OP_TRANSPOSE),
            entry("FILTER_TABLE_FUNCTION_TRANSPOSE", CoreRules.FILTER_TABLE_FUNCTION_TRANSPOSE),
            entry("PROJECT_AGGREGATE_MERGE", CoreRules.PROJECT_AGGREGATE_MERGE),
            entry("PROJECT_MERGE", CoreRules.PROJECT_MERGE),
            entry("PROJECT_REDUCE_EXPRESSIONS", MyRules.PROJECT_REDUCE_EXPRESSIONS),
            entry("PROJECT_REMOVE", CoreRules.PROJECT_REMOVE),
            entry("PROJECT_SUB_QUERY_TO_CORRELATE", CoreRules.PROJECT_SUB_QUERY_TO_CORRELATE),
            entry("FILTER_SUB_QUERY_TO_CORRELATE", CoreRules.FILTER_SUB_QUERY_TO_CORRELATE),
            entry("JOIN_SUB_QUERY_TO_CORRELATE", CoreRules.JOIN_SUB_QUERY_TO_CORRELATE),
            entry("PROJECT_JOIN_JOIN_REMOVE", CoreRules.PROJECT_JOIN_JOIN_REMOVE),
            entry("PROJECT_JOIN_REMOVE", CoreRules.PROJECT_JOIN_REMOVE),
            entry("JOIN_CONDITION_PUSH", CoreRules.JOIN_CONDITION_PUSH),
            entry("JOIN_PUSH_TRANSITIVE_PREDICATES", CoreRules.JOIN_PUSH_TRANSITIVE_PREDICATES),
            entry("JOIN_REDUCE_EXPRESSIONS", MyRules.JOIN_REDUCE_EXPRESSIONS),
            entry("SORT_REMOVE", CoreRules.SORT_REMOVE),
            entry("SORT_REMOVE_CONSTANT_KEYS", CoreRules.SORT_REMOVE_CONSTANT_KEYS),
            entry("UNION_REMOVE", CoreRules.UNION_REMOVE),
            entry("UNION_PULL_UP_CONSTANTS", CoreRules.UNION_PULL_UP_CONSTANTS),
            entry("AGGREGATE_VALUES", CoreRules.AGGREGATE_VALUES),
            entry("FILTER_VALUES_MERGE", CoreRules.FILTER_VALUES_MERGE),
            entry("PROJECT_VALUES_MERGE", CoreRules.PROJECT_VALUES_MERGE),
            entry("PROJECT_FILTER_VALUES_MERGE", CoreRules.PROJECT_FILTER_VALUES_MERGE),
            entry("WINDOW_REDUCE_EXPRESSIONS", MyRules.WINDOW_REDUCE_EXPRESSIONS)
    );

    public static final Map<String, RelOptRule> EXPLORE_RULES = Map.ofEntries(
            entry("AGGREGATE_EXPAND_DISTINCT_AGGREGATES", CoreRules.AGGREGATE_EXPAND_DISTINCT_AGGREGATES),
            entry(
                    "AGGREGATE_EXPAND_DISTINCT_AGGREGATES_TO_JOIN",
                    CoreRules.AGGREGATE_EXPAND_DISTINCT_AGGREGATES_TO_JOIN
            ),
            entry("AGGREGATE_FILTER_TRANSPOSE", CoreRules.AGGREGATE_FILTER_TRANSPOSE),
            entry("AGGREGATE_JOIN_TRANSPOSE_EXTENDED", CoreRules.AGGREGATE_JOIN_TRANSPOSE_EXTENDED),
            entry("AGGREGATE_REDUCE_FUNCTIONS", CoreRules.AGGREGATE_REDUCE_FUNCTIONS),
            entry("AGGREGATE_UNION_TRANSPOSE", CoreRules.AGGREGATE_UNION_TRANSPOSE),
            entry("AGGREGATE_UNION_AGGREGATE_FIRST", CoreRules.AGGREGATE_UNION_AGGREGATE_FIRST),
            entry("AGGREGATE_UNION_AGGREGATE_SECOND", CoreRules.AGGREGATE_UNION_AGGREGATE_SECOND),
            entry("PROJECT_CORRELATE_TRANSPOSE", CoreRules.PROJECT_CORRELATE_TRANSPOSE),
            entry("PROJECT_FILTER_TRANSPOSE", PROJECT_FILTER_TRANSPOSE),
            entry("PROJECT_TO_LOGICAL_PROJECT_AND_WINDOW", CoreRules.PROJECT_TO_LOGICAL_PROJECT_AND_WINDOW),
            entry("PROJECT_JOIN_TRANSPOSE", CoreRules.PROJECT_JOIN_TRANSPOSE),
            entry("PROJECT_SET_OP_TRANSPOSE", CoreRules.PROJECT_SET_OP_TRANSPOSE),
            entry("PROJECT_WINDOW_TRANSPOSE", CoreRules.PROJECT_WINDOW_TRANSPOSE),
            entry("JOIN_ADD_REDUNDANT_SEMI_JOIN", CoreRules.JOIN_ADD_REDUNDANT_SEMI_JOIN),
            entry("JOIN_EXTRACT_FILTER", CoreRules.JOIN_EXTRACT_FILTER),
            entry("JOIN_PROJECT_BOTH_TRANSPOSE_INCLUDE_OUTER", CoreRules.JOIN_PROJECT_BOTH_TRANSPOSE_INCLUDE_OUTER),
            entry("JOIN_PROJECT_LEFT_TRANSPOSE_INCLUDE_OUTER", CoreRules.JOIN_PROJECT_LEFT_TRANSPOSE_INCLUDE_OUTER),
            entry(
                    "JOIN_PROJECT_RIGHT_TRANSPOSE_INCLUDE_OUTER",
                    CoreRules.JOIN_PROJECT_RIGHT_TRANSPOSE_INCLUDE_OUTER
            ),
            entry("JOIN_DERIVE_IS_NOT_NULL_FILTER_RULE", CoreRules.JOIN_DERIVE_IS_NOT_NULL_FILTER_RULE),
            entry("JOIN_PUSH_EXPRESSIONS", CoreRules.JOIN_PUSH_EXPRESSIONS),
            entry("JOIN_TO_CORRELATE", CoreRules.JOIN_TO_CORRELATE),
            entry("JOIN_LEFT_UNION_TRANSPOSE", CoreRules.JOIN_LEFT_UNION_TRANSPOSE),
            entry("JOIN_RIGHT_UNION_TRANSPOSE", CoreRules.JOIN_RIGHT_UNION_TRANSPOSE),
            entry("SEMI_JOIN_FILTER_TRANSPOSE", CoreRules.SEMI_JOIN_FILTER_TRANSPOSE),
            entry("SEMI_JOIN_PROJECT_TRANSPOSE", CoreRules.SEMI_JOIN_PROJECT_TRANSPOSE),
            entry("SEMI_JOIN_JOIN_TRANSPOSE", CoreRules.SEMI_JOIN_JOIN_TRANSPOSE),
            entry("SORT_JOIN_TRANSPOSE", CoreRules.SORT_JOIN_TRANSPOSE),
            entry("SORT_PROJECT_TRANSPOSE", CoreRules.SORT_PROJECT_TRANSPOSE),
            entry("SORT_UNION_TRANSPOSE", CoreRules.SORT_UNION_TRANSPOSE),
            entry("SORT_UNION_TRANSPOSE_MATCH_NULL_FETCH", CoreRules.SORT_UNION_TRANSPOSE_MATCH_NULL_FETCH),
            entry("UNION_TO_DISTINCT", CoreRules.UNION_TO_DISTINCT),
            entry("INTERSECT_TO_DISTINCT", CoreRules.INTERSECT_TO_DISTINCT)
    );

    public static final Map<String, RelOptRule> SEMI_JOIN_RULES = Map.ofEntries(
            entry("JOIN_ADD_REDUNDANT_SEMI_JOIN", CoreRules.JOIN_ADD_REDUNDANT_SEMI_JOIN),
            entry("SEMI_JOIN_FILTER_TRANSPOSE", CoreRules.SEMI_JOIN_FILTER_TRANSPOSE),
            entry("SEMI_JOIN_PROJECT_TRANSPOSE", CoreRules.SEMI_JOIN_PROJECT_TRANSPOSE),
            entry("SEMI_JOIN_JOIN_TRANSPOSE", CoreRules.SEMI_JOIN_JOIN_TRANSPOSE)
    );

    public static final Map<String, RelOptRule> USED_RULES = Stream.concat(
            NORMAL_RULES.entrySet().stream(),
            EXPLORE_RULES.entrySet().stream()
    ).collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue));

    public static final List<RelOptRule> PRUNE_EMPTY_RULES =
            Arrays.asList(
                    PruneEmptyRules.UNION_INSTANCE,
                    PruneEmptyRules.MINUS_INSTANCE,
                    PruneEmptyRules.INTERSECT_INSTANCE,
                    PruneEmptyRules.PROJECT_INSTANCE,
                    PruneEmptyRules.FILTER_INSTANCE,
                    PruneEmptyRules.SORT_INSTANCE,
                    PruneEmptyRules.SORT_FETCH_ZERO_INSTANCE,
                    PruneEmptyRules.AGGREGATE_INSTANCE,
                    PruneEmptyRules.JOIN_LEFT_INSTANCE,
                    PruneEmptyRules.JOIN_RIGHT_INSTANCE,
                    PruneEmptyRules.CORRELATE_LEFT_INSTANCE,
                    PruneEmptyRules.CORRELATE_RIGHT_INSTANCE
            );
}
