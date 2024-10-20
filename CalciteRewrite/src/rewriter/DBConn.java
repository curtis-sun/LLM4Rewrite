package rewriter;

import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;

import java.math.BigDecimal;
import java.sql.*;


public class DBConn {
  private String host;
  private String port;
  private String user;
  private String password;
  public String dbname;
  private Connection conn;
  private String DBDriver;

  public DBConn(String host, String port, String user, String password, String dbname, String DBDriver)
          throws Exception {
    this.host = host;
    this.port = port;
    this.user = user;
    this.password = password;
    this.dbname = dbname;
    this.DBDriver = DBDriver;
    getConn();
  }

  private void getConn() throws Exception{
    Class.forName(this.DBDriver);
    this.conn = DriverManager.getConnection("jdbc:postgresql://" + host + ":" + port + "/" + dbname, user, password);
  }

  public double getCost(String sql) {
    double cost = Double.MAX_VALUE;
    try {
      Statement stmt = this.conn.createStatement();
      stmt.execute("SET enable_indexscan = off;");
      boolean success = stmt.execute("explain (FORMAT JSON) " + sql);
      if (success) {
        ResultSet res = stmt.getResultSet();
        res.next();
        String s = res.getArray(1).toString().strip();
        JSONArray jarray = (JSONArray) JSONObject.parse(s);
        JSONObject jobject = (JSONObject) jarray.get(0);
        jobject = (JSONObject) jobject.get("Plan");
        cost = ((BigDecimal) jobject.get("Total Cost")).doubleValue();
        stmt.close();
      } else {
        System.out.println("Failed to get SQL cost: " + sql);
      }
    } catch (SQLException e) {
//      e.printStackTrace();
      cost = Double.MAX_VALUE;
    }
    return cost;
  }
}