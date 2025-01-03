package learned;

import org.apache.calcite.rel.RelNode;
import org.apache.calcite.test.RelOptFixture;

import java.util.*;

import static learned.MyRules.RULE_SEQS;
import static learned.MyRules.RULE_TYPES;

public class Node {
  public String sql;
  public RelNode rel;
  public List<String> usedRules;

  public double originCost;
  public double cost;
  double gamma;
  public double reward;
  int visits = 1;

  public Node parent;
  public List<Node> children;

  Rewriter rewriter;
  RelOptFixture fixture;

  public Node(String sql,
              RelNode rel,
              List<String> usedRules,
              double originCost,
              double cost,
              double gamma,
              Node parent,
              Rewriter rewriter,
              RelOptFixture fixture
              ) {
    this.sql = sql;
    this.rel = rel;
    this.usedRules = usedRules;

    this.originCost = originCost;
    this.cost = cost;
    this.gamma = gamma;
    this.reward = originCost - cost;

    this.parent = parent;
    this.children = new ArrayList<>();

    this.rewriter = rewriter;
    this.fixture = fixture;
    rewriter.plans.add(rel.explain());
  }
  public void addChild(String sql, RelNode relNode, double cost, List<String> usedRules) {
    Node child = new Node(sql, relNode, usedRules, originCost, cost, gamma, this, rewriter, fixture);
    this.children.add(child);
  }

  public boolean ruleCheck(RelNode relNode, Class clazz) {
    if (clazz.isInstance(relNode)) {
      return true;
    }
    List<RelNode> children = relNode.getInputs();
    for (RelNode child: children) {
      if (ruleCheck(child, clazz)) {
        return true;
      }
    }
    return false;
  }

  public void nodeChildren() {
    for(String rule: RULE_SEQS.keySet()) {
      if (!ruleCheck(this.rel, RULE_TYPES.get(rule))) {
        continue;
      }

      RewriteResult res = rewriter.rewrite(this.rel, rule, fixture);
      if (res == null) {
        continue;
      }
      RelNode relAfter = res.rel;
      List<String> usedRules = res.rules;
      if (this.rewriter.plans.contains(relAfter.explain())) {
        continue;
      }

      String sqlAfter = res.sql;
      if (sqlAfter == null || rewriter.getCostRecordFromSql(sqlAfter) == Double.MAX_VALUE) {
        continue;
      }
      double newCost = Rewriter.getCostRecordFromRelNode(relAfter);
      if (newCost <= this.originCost) {
        // todo rule selection
        this.addChild(sqlAfter, relAfter, newCost, usedRules);
      }
    }
  }

  public boolean isTerminal() {
    return this.children == null || this.children.size() == 0;
  }

  public Node UTCSEARCH(Node root, int budget) {
    root.nodeChildren();
    for (int i = 0; i < budget; i ++) {
      Node front = TREEPOLICY(root);
      front.nodeChildren();
      double reward = FINDBESTREWARD(front);
      BACKUP(front, reward);
    }
    Node bestNode = FINDBESTNODE(root);
    return bestNode;
  }

  private double FINDBESTREWARD(Node node) {
    double reward = 0;
    for (Node c: node.children) {
      if (c.reward > reward) {
        reward = c.reward;
      }
    }
    return reward;
  }

  private Node BESTCHILD(Node node) {
    double bestScore = 0;
    List<Node> bestChildren = new ArrayList<>();
    for (Node c: node.children) {
      double exploit = c.reward / c.visits;
      double explore = Math.sqrt(2 * Math.log(node.visits) / c.visits);
      double score = exploit + node.gamma * explore;
      if (score > bestScore) {
        bestChildren.clear();
        bestChildren.add(c);
        bestScore = score;
      }
      else if (score == bestScore) {
        bestChildren.add(c);
      }
    }
    Random random = new Random();
    int i = random.nextInt(bestChildren.size());
    return bestChildren.get(i);
  }

  private Node TREEPOLICY(Node root) {
    Node node = root;
    while (!node.isTerminal()) {
      node = BESTCHILD(node);
    }
    return node;
  }

  private void BACKUP(Node node, double reward) {
    while(node != null) {
      node.visits += 1;
      if (reward > node.reward){
        node.reward = reward;
      }
      node = node.parent;
    }
  }

  private Node FINDBESTNODE(Node bestNode) {
    while (!bestNode.isTerminal()) {
      double bestScore = 0;
      List<Node> bestChildren = new ArrayList<>();
      for (Node c: bestNode.children){
        double score = c.reward;
        if (score > bestScore){
          bestChildren.clear();
          bestChildren.add(c);
          bestScore = score;
        }
        else if (score == bestScore){
          bestChildren.add(c);
        }
      }
      Random random = new Random();
      int i = random.nextInt(bestChildren.size());
      bestNode = bestChildren.get(i);
    }
    return bestNode;
  }
}
