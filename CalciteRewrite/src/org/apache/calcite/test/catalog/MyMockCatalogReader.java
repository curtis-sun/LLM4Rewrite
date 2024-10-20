package org.apache.calcite.test.catalog;

import com.alibaba.innodb.java.reader.column.ColumnType;
import com.alibaba.innodb.java.reader.schema.Column;
import com.alibaba.innodb.java.reader.schema.KeyMeta;
import com.alibaba.innodb.java.reader.schema.TableDef;
import database.ColumnTypeToSqlTypeConversionRules;
import org.apache.calcite.rel.type.RelDataType;
import org.apache.calcite.rel.type.RelDataTypeFactory;
import org.apache.calcite.sql.type.SqlTypeName;
import org.apache.calcite.util.Pair;
import org.checkerframework.checker.nullness.qual.NonNull;

import java.util.*;

public class MyMockCatalogReader extends MockCatalogReader {

    public class TableInfo {
        Map<String, TableDef> tables;
        public TableInfo(Map<String, TableDef> t) {
            tables = t;
        }
    }

    static final ColumnTypeToSqlTypeConversionRules COLUMN_TYPE_TO_SQL_TYPE =
            ColumnTypeToSqlTypeConversionRules.instance();


    protected RelDataType getColumnType(Column column){
        RelDataType type;

        final SqlTypeName sqlTypeName =
                COLUMN_TYPE_TO_SQL_TYPE.lookup(column.getType());
        final int precision;
        final int scale;
        switch (column.getType()) {
            case ColumnType.TIMESTAMP:
            case ColumnType.TIME:
            case ColumnType.DATETIME:
                precision = column.getPrecision();
                scale = 0;
                break;
            default:
                precision = column.getPrecision();
                scale = column.getScale();
                break;
        }

        if (sqlTypeName.allowsPrecScale(true, true)
                && column.getPrecision() >= 0
                && column.getScale() >= 0) {
            type = typeFactory.createSqlType(sqlTypeName, precision, scale);
        } else if (sqlTypeName.allowsPrecNoScale() && precision >= 0) {
            type = typeFactory.createSqlType(sqlTypeName, precision);
        } else {
            assert sqlTypeName.allowsNoPrecNoScale();
            type = typeFactory.createSqlType(sqlTypeName);
        }

        final boolean nullable = column.isNullable();
        if (type.isNullable() != nullable) {
            type = typeFactory.createTypeWithNullability(type, nullable);
        }

        return type;
    }

    protected Map<String, TableInfo> initTables() {
        return new HashMap<>();
    }

    /**
     * Creates a MockCatalogReader.
     *
     * <p>Caller must then call {@link #init} to populate with data;
     * constructor is protected to encourage you to define a {@code create}
     * method in each concrete sub-class.
     *
     * @param typeFactory   Type factory
     * @param caseSensitive
     */
    protected MyMockCatalogReader(RelDataTypeFactory typeFactory, boolean caseSensitive) {
        super(typeFactory, caseSensitive);
    }

    public static @NonNull MyMockCatalogReader create(
            RelDataTypeFactory typeFactory, boolean caseSensitive) {
        return new MyMockCatalogReader(typeFactory, caseSensitive).init();
    }

    @Override public MyMockCatalogReader init() {
        Map<String, TableInfo> tableInfoMap = initTables();

        for (String database: tableInfoMap.keySet()){
            MockSchema schema = new MockSchema(database);
            registerSchema(schema);

            Map<String, TableDef> tables = tableInfoMap.get(database).tables;
            for (String tableName : tables.keySet()) {
                MockTable table =
                        MockTable.create(this, schema, tableName.toLowerCase(Locale.ROOT), false, 100);

                TableDef tableDef = tables.get(tableName);
                List<String> primaryKeyColumns = tableDef.getPrimaryKeyColumnNames();
                for (Column column: tableDef.getColumnList()){
                    RelDataType type = getColumnType(column);
                    boolean isKey = primaryKeyColumns.contains(column.getName());
                    table.addColumn(column.getName().toLowerCase(Locale.ROOT), type, isKey);
                }

                List<KeyMeta> secondaryKeyMetaList = tableDef.getSecondaryKeyMetaList();
                for (KeyMeta meta: secondaryKeyMetaList){
                    if (meta.getType() == KeyMeta.Type.UNIQUE_KEY
                     || meta.getType() == KeyMeta.Type.UNIQUE_INDEX
                     || meta.getType() == KeyMeta.Type.KEY) {
                        List<Pair<String, RelDataType>> keyColumnNameTypes = new ArrayList<>();
                        for (Column col: meta.getKeyColumns()) {
                            keyColumnNameTypes.add(Pair.of(col.getName().toLowerCase(Locale.ROOT), getColumnType(col)));
                        }
                        table.addUniqueConstraint(keyColumnNameTypes);
                    }
                }
                registerTable(table);
            }
        }

        return this;
    }
}
