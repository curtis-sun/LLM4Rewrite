package rewriter;

import com.alibaba.innodb.java.reader.schema.TableDef;
import com.alibaba.innodb.java.reader.schema.provider.TableDefProvider;
import com.alibaba.innodb.java.reader.schema.provider.impl.SqlTableDefProvider;
import org.apache.calcite.avatica.util.Casing;
import org.apache.calcite.config.CalciteConnectionConfig;
import org.apache.calcite.plan.Contexts;
import org.apache.calcite.sql.SqlDialect;
import org.apache.calcite.sql.dialect.PostgresqlSqlDialect;
import org.apache.calcite.sql.fun.SqlLibrary;
import org.apache.calcite.sql.fun.SqlLibraryOperatorTableFactory;
import org.apache.calcite.test.RelOptFixture;
import org.apache.calcite.test.catalog.MyMockCatalogReader;

import java.util.*;

public class SqlIo {
    public static SqlLibrary getOperatorTable(String database){
        return SqlLibrary.of(database.toLowerCase(Locale.ROOT).trim());
    }

    public static SqlDialect.DatabaseProduct getProduct(String productName) {
        final String upperProductName =
                productName.toUpperCase(Locale.ROOT).trim();
        switch (upperProductName) {
            case "ACCESS":
                return SqlDialect.DatabaseProduct.ACCESS;
            case "APACHE DERBY":
                return SqlDialect.DatabaseProduct.DERBY;
            case "CLICKHOUSE":
                return SqlDialect.DatabaseProduct.CLICKHOUSE;
            case "DBMS:CLOUDSCAPE":
                return SqlDialect.DatabaseProduct.DERBY;
            case "EXASOL":
                return SqlDialect.DatabaseProduct.EXASOL;
            case "FIREBOLT":
                return SqlDialect.DatabaseProduct.FIREBOLT;
            case "HIVE":
                return SqlDialect.DatabaseProduct.HIVE;
            case "INGRES":
                return SqlDialect.DatabaseProduct.INGRES;
            case "INTERBASE":
                return SqlDialect.DatabaseProduct.INTERBASE;
            case "LUCIDDB":
                return SqlDialect.DatabaseProduct.LUCIDDB;
            case "ORACLE":
                return SqlDialect.DatabaseProduct.ORACLE;
            case "PHOENIX":
                return SqlDialect.DatabaseProduct.PHOENIX;
            case "PRESTO":
            case "AWS.ATHENA":
                return SqlDialect.DatabaseProduct.PRESTO;
            case "MSSQL":
                return SqlDialect.DatabaseProduct.MSSQL;
            case "MYSQL (INFOBRIGHT)":
                return SqlDialect.DatabaseProduct.INFOBRIGHT;
            case "MYSQL":
                return SqlDialect.DatabaseProduct.MYSQL;
            case "REDSHIFT":
                return SqlDialect.DatabaseProduct.REDSHIFT;
            case "SPARK":
                return SqlDialect.DatabaseProduct.SPARK;
            default:
                break;
        }
        // Now the fuzzy matches.
        if (productName.startsWith("DB2")) {
            return SqlDialect.DatabaseProduct.DB2;
        } else if (upperProductName.contains("FIREBIRD")) {
            return SqlDialect.DatabaseProduct.FIREBIRD;
        } else if (productName.startsWith("Informix")) {
            return SqlDialect.DatabaseProduct.INFORMIX;
        } else if (upperProductName.contains("NETEZZA")) {
            return SqlDialect.DatabaseProduct.NETEZZA;
        } else if (upperProductName.contains("PARACCEL")) {
            return SqlDialect.DatabaseProduct.PARACCEL;
        } else if (productName.startsWith("HP Neoview")) {
            return SqlDialect.DatabaseProduct.NEOVIEW;
        } else if (upperProductName.contains("POSTGRE")) {
            return SqlDialect.DatabaseProduct.POSTGRESQL;
        } else if (upperProductName.contains("SQL SERVER")) {
            return SqlDialect.DatabaseProduct.MSSQL;
        } else if (upperProductName.contains("SYBASE")) {
            return SqlDialect.DatabaseProduct.SYBASE;
        } else if (upperProductName.contains("TERADATA")) {
            return SqlDialect.DatabaseProduct.TERADATA;
        } else if (upperProductName.contains("HSQL")) {
            return SqlDialect.DatabaseProduct.HSQLDB;
        } else if (upperProductName.contains("H2")) {
            return SqlDialect.DatabaseProduct.H2;
        } else if (upperProductName.contains("VERTICA")) {
            return SqlDialect.DatabaseProduct.VERTICA;
        } else if (upperProductName.contains("GOOGLE BIGQUERY")
                || upperProductName.contains("GOOGLE BIG QUERY")) {
            return SqlDialect.DatabaseProduct.BIG_QUERY;
        } else {
            return SqlDialect.DatabaseProduct.UNKNOWN;
        }
    }
    public static RelOptFixture inputSql(String sql, List<String> createTables, String database) {
        sql = sql.replace(";", "");
        sql = sql.replaceAll("--.*?\\n", " ");
        sql = sql.replaceAll("\\n", " ");
        sql = sql.replaceAll("!=", "<>");
        return RelOptFixture.DEFAULT.sql(sql)
                .withCatalogReaderFactory((typeFactory, caseSensitive) ->
                        new MyMockCatalogReader(typeFactory, caseSensitive) {
                            @Override protected Map<String, TableInfo> initTables() {
                                final Map<String, TableInfo> tableInfoMap = new HashMap<>();
                                String database = "SALES";

                                TableDefProvider provider = new SqlTableDefProvider(createTables);
                                Map<String, TableDef> tables = provider.load();
                                tableInfoMap.put(database, new TableInfo(tables));
                                return tableInfoMap;
                            }
                        }.init())
                .withFactory(f -> f.withOperatorTable(opTab ->
                                SqlLibraryOperatorTableFactory.INSTANCE.getOperatorTable(
                                        SqlLibrary.STANDARD, getOperatorTable(database)))
                        .withParserConfig(parserConfig -> getProduct(database).getDialect().configureParser(parserConfig).withCaseSensitive(false))
                )
                .withContext(c -> Contexts.of(CalciteConnectionConfig.DEFAULT, c));
    }

    public static String outputSql(String sql){
        String outputSql = sql
                .replaceAll("[\"`]CATALOG[\"`]\\.", "")
                .replaceAll("[\"`]SALES[\"`]\\.", "")
                .replaceAll("VARCHAR CHARACTER SET \".+?\"", "VARCHAR")
                .replaceAll("TIMESTAMP\\(0\\)", "TIMESTAMP")
                .replaceAll("CHAR\\(0\\)", "CHAR");
        while (true) {
            sql = outputSql.replaceAll("CAST\\(((?:(?! AS ).)+?) AS DECIMAL\\(7, 2\\)\\)", "$1")
                    .replaceAll("CAST\\(([A-Za-z]+\\([\"`].+?[\"`]\\) FILTER \\(WHERE [\"`].+?[\"`]\\)) AS INTEGER\\)", "$1")
                    .replaceAll("CAST\\(([\"`].+?[\"`]\\.[\"`].+?[\"`] \\* [\"`].+?[\"`]\\.[\"`].+?[\"`]) AS INTEGER\\)", "$1");
            if (sql.equals(outputSql)) {
                break;
            } else {
                outputSql = sql;
            }
        }

        if (!outputSql.endsWith(";")){
            outputSql += ";";
        }
        return outputSql;
    }
}
