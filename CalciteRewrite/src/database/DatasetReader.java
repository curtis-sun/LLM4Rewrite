package database;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.*;
import java.util.stream.Stream;

public class DatasetReader {
    public static String readFile(String pathName) {
        try {
            List<String> lines = new ArrayList<>();
            File myObj = new File(pathName);
            Scanner myReader = new Scanner(myObj);
            while (myReader.hasNextLine()) {
                String data = myReader.nextLine();
                lines.add(data);
            }
            myReader.close();
            return String.join("\n", lines);
        } catch (FileNotFoundException e) {
            System.out.println("Failed to read file: " + pathName);
            e.printStackTrace();
            return null;
        }
    }

    public static Map<String, List<String>> readQueries(String pathName) {
        List<String> templates = Stream.of(new File(pathName).listFiles())
                .filter(File::isDirectory)
                .map(File::getName)
                .toList();
        Map<String, List<String>> queries = new HashMap<>();
        for (String template: templates) {
            final String templatePathName = String.join("/", Arrays.asList(
                    pathName,
                    template
            ));
            List<String> names = Stream.of(new File(templatePathName).listFiles())
                    .map(File::getName)
                    .filter(name -> name.endsWith(".sql"))
                    .toList();
            for (String name: names) {
                final String sqlPathName = String.join("/", Arrays.asList(
                        templatePathName,
                        name
                ));
                final String sqls = readFile(sqlPathName);
                queries.put(
                        name.substring(0, name.length() - 4),
                        Arrays.stream(sqls.split(";"))
                                .filter(x -> ! x.strip().equals(""))
                                .toList()
                );
            }
        }
        return queries;
    }
}
