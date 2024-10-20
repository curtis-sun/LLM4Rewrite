package learned;
import org.apache.calcite.rel.rel2sql.RelToSqlConverter;
import rewriter.DBConn;
import com.google.common.collect.ImmutableSet;
import org.apache.calcite.plan.hep.HepMatchOrder;
import org.apache.calcite.plan.hep.HepPlanner;
import org.apache.calcite.plan.hep.HepProgramBuilder;
import org.apache.calcite.rel.rules.CoreRules;
import org.apache.calcite.sql.SqlDialect;
import org.apache.calcite.sql.pretty.SqlPrettyWriter;
import org.apache.calcite.test.RelOptFixture;
import org.apache.calcite.plan.*;
import org.apache.calcite.rel.RelNode;

import java.util.*;

import static learned.MyRules.RULE_SEQS;
import static rewriter.SqlIo.getProduct;
import static rewriter.SqlIo.outputSql;

public class Rewriter {
  public DBConn db;
  public SqlDialect dialect;

  public Set<String> plans;

  public Rewriter(DBConn db, SqlDialect dialect) {
    this.db = db;
    this.dialect = dialect;
    this.plans = new HashSet<>();
  }

  public static List<String> collectUsedRules(Node node) {
    List<String> usedRules = new ArrayList<>();
    Node curNode = node;
    while (curNode != null) {
      usedRules.addAll(0, curNode.usedRules);
      curNode = curNode.parent;
    }
    return usedRules;
  }

  public static RelOptCost getCostFromRelNode(RelNode rel_node) {
    Deque<RelNode> stack = new LinkedList<RelNode>();
    stack.add(rel_node);
    RelOptCost tolCost = new RelOptCostImpl(0);
    while (!stack.isEmpty()) {
      RelNode node = stack.pop();
      tolCost = tolCost.plus(node.computeSelfCost(node.getCluster().getPlanner(), node.getCluster().getMetadataQuery()));
      stack.addAll(node.getInputs());
    }
    return tolCost;
  }

  // first layer: multi-head attention + fully-connected
  // second layer: normalization + fully-connected
  // third layer: multi-head attention + fully-connected (relu)

  public static double getCostRecordFromRelNode(RelNode rel_node) {
    return getCostFromRelNode(rel_node).getRows()+getCostFromRelNode(rel_node).getCpu()*0.01+getCostFromRelNode(rel_node).getIo()*4; // these metrics should have been obtained from db!!
  }

  public double getCostRecordFromSql(String sql) {
    return db.getCost(outputSql(sql));
  }

  //RBO optimizing with HepPlanner
  public RewriteResult rewrite(RelNode relNode, String ruleName, RelOptFixture fixture) {
    RewriteResult res = new RewriteResult();
    Map<String, RelOptRule> rules = RULE_SEQS.get(ruleName);

    res.rel = relNode;
    for (int i = 0; i < 5; i ++) {
      for (String curRuleName: rules.keySet()) {
        RelOptRule rule = rules.get(curRuleName);
        try {
          HepProgramBuilder builder = new HepProgramBuilder();
          builder.addRuleInstance(rule);
          HepPlanner hepPlanner = new HepPlanner(builder.addMatchOrder(HepMatchOrder.TOP_DOWN).build());

          boolean lateDecorrelate = ImmutableSet.of(
                          CoreRules.JOIN_SUB_QUERY_TO_CORRELATE,
                          CoreRules.PROJECT_SUB_QUERY_TO_CORRELATE,
                          CoreRules.FILTER_SUB_QUERY_TO_CORRELATE)
                  .contains(rule);

          final RelNode relAfter = fixture
                  .withPlanner(hepPlanner)
                  .withLateDecorrelate(lateDecorrelate)
                  .findBest(res.rel);
          if (!relAfter.explain().equals(res.rel.explain())) {
            res.rules.add(curRuleName);
            res.rel = relAfter;
          }
        } catch (Exception ignored) {}
      }
    }

    try {
      res.sql = (new SqlPrettyWriter()).format(new RelToSqlConverter(dialect).visitRoot(res.rel).asStatement());
    }  catch (Exception e) {
      // e.printStackTrace();
    }
    return res;
  }
}


