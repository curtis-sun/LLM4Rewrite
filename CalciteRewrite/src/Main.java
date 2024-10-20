import database.DatasetReader;
import org.apache.calcite.util.Pair;
import org.json.simple.JSONObject;
import rewriter.DBConn;
import rewriter.RewriteResult;
import rewriter.Rewriter;

import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

import static rewriter.SqlIo.outputSql;

public class Main {
    public static double getCost(String sql, DBConn dbConn) {
        return dbConn.getCost(sql);
    }

    public static void main(String[] args) {}
}
