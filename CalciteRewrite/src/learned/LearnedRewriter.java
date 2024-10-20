package learned;

import org.apache.calcite.rel.RelNode;
import org.apache.calcite.sql.dialect.PostgresqlSqlDialect;
import org.apache.calcite.test.RelOptFixture;
import org.json.simple.JSONObject;
import rewriter.DBConn;

import java.util.ArrayList;
import java.util.List;

import static learned.Rewriter.collectUsedRules;
import static rewriter.SqlIo.inputSql;
import static rewriter.SqlIo.outputSql;

public class LearnedRewriter {
    public static JSONObject learnedRewrite(String query, List<String> createTables, int budget, String host, String port, String user, String password, String dbname) {
        JSONObject dataJson = new JSONObject();
        //DB Config
        String dbDriver = "org.postgresql.Driver";

        DBConn dbConn;
        try {
            dbConn = new DBConn(host, port, user, password, dbname, dbDriver);
        } catch (Exception e) {
            e.printStackTrace();
            return dataJson;
        }

        long startTime = System.currentTimeMillis();
        RelOptFixture fixture = inputSql(query, createTables, "PostgreSQL");
        Rewriter rewriter = new Rewriter(dbConn, PostgresqlSqlDialect.DEFAULT);
        final RelNode relBefore = fixture.toRel();
        final double costBefore = rewriter.getCostRecordFromSql(query);
        final Node nodeBefore = new Node(query, relBefore, new ArrayList<>(), costBefore, costBefore, costBefore, null, rewriter, fixture);
        final Node bestNode = nodeBefore.UTCSEARCH(nodeBefore, budget);
        long time = System.currentTimeMillis() - startTime;
        final List<String> usedRules = collectUsedRules(bestNode);
        double costAfter = bestNode.cost;
        String sqlAfter = bestNode.sql;

        dataJson.put("input_cost", String.format("%.4f", costBefore == Double.MAX_VALUE ? -1 : costBefore));
        dataJson.put("input_sql", query);
        dataJson.put("output_cost", String.format("%.4f", costAfter == Double.MAX_VALUE ? -1 : costAfter));
        dataJson.put("output_sql", outputSql(sqlAfter));
        dataJson.put("used_rules", usedRules);
        dataJson.put("time", time);
        return dataJson;
    }
}
