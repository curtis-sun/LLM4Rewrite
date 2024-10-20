package rewriter;

import org.apache.calcite.rel.RelNode;

import java.util.ArrayList;
import java.util.List;

public class RewriteResult {
    public List<String> rules = new ArrayList<>();
    public RelNode r1 = null;
    public RelNode r2 = null;
    public RelNode r3 = null;
    public String sql = null;

    public Long time = null;
}
