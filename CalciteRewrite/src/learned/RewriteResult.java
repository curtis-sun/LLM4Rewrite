package learned;

import org.apache.calcite.rel.RelNode;

import java.util.ArrayList;
import java.util.List;

public class RewriteResult {
    public RelNode rel = null;
    public String sql = null;
    public List<String> rules = new ArrayList<>();
}