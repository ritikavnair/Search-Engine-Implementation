import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.Scanner;

import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.core.SimpleAnalyzer;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field;
import org.apache.lucene.document.StringField;
import org.apache.lucene.document.TextField;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.index.Term;
import org.apache.lucene.queryparser.classic.QueryParser;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.ScoreDoc;
import org.apache.lucene.search.TopScoreDocCollector;
import org.apache.lucene.store.FSDirectory;
import org.apache.lucene.util.Version;

/**
 * To create Apache Lucene index in a folder and add files into this index based
 * on the input documents.
 */
public class Lucene {
	
	private static Analyzer sAnalyzer = new SimpleAnalyzer(Version.LUCENE_47);
	private IndexWriter writer;
	private ArrayList<File> queue = new ArrayList<File>();

	public static void main(String[] args) throws IOException {

		// Modify this path to your path containing the 'TokenizedFile' directory.
		String inputLocation = "/Users/grishmathakkar/Desktop/SEM1/IR/IR PROJECT/Lucene";
		String indexLocation = null;		
		Lucene indexer = null;

		try {
			//Index will be generated in the indexLocation path
			indexLocation = inputLocation + "/Lucene-Output/index_files";				

			// Remove any existing index, create fresh ones.
			File indexDirectory = new File(indexLocation);
			if (indexDirectory.isDirectory()) {
				for (File f : indexDirectory.listFiles()) {
					if (f.exists()) {
						f.delete();
					}
				}
			}

			// Initialize the indexer.
			indexer = new Lucene(indexLocation);

			// Add files into the index
			indexer.indexFileOrDirectory(inputLocation+"/TokenizedFile");
		}
		catch (Exception e) {
			System.out.println("Error indexing " + inputLocation + " : "
					+ e.getMessage());
		}

		// ===================================================
		// after adding, we always have to call the
		// closeIndex, otherwise the index is not created
		// ===================================================
		indexer.closeIndex();

		// =========================================================
		// Now search
		// =========================================================
		IndexReader reader = DirectoryReader.open(FSDirectory.open
				(new File(indexLocation)));
		IndexSearcher searcher = new IndexSearcher(reader);

		int queryId = 0;
		try {
			// Extracts the queries from queries.txt and ranks the top 100 documents
			Scanner queryReader = new Scanner(new File(inputLocation + "/queries.txt"));
			String fileName2="LuceneOutput.txt";
			BufferedWriter writer2= new BufferedWriter(new FileWriter(fileName2, true));
		    writer2.append(' ');
			while (queryReader.hasNextLine()) {
				// Fetching top 100 results for each query
				TopScoreDocCollector collector = TopScoreDocCollector.create(100, true);
				String queryText = queryReader.nextLine();
				queryId+=1;


				Query query = new QueryParser(Version.LUCENE_47, 
						"contents",
						sAnalyzer).parse(queryText);
				searcher.search(query, collector); 
				ScoreDoc[] hits = collector.topDocs().scoreDocs;

				// Save the results into a textfile for each query.
				System.out.println("Found " + hits.length + " hits.");
				for (int i = 0; i <  Math.min(100, hits.length); ++i) {
					int docId = hits[i].doc;
					Document d = searcher.doc(docId);
					String docName = d.get("filename");
					//Removing .txt
					docName = docName.substring(0, docName.length() - 4); 
					String result = queryId + " Q0 " + docName 
							+ " " + (i + 1) + " " + hits[i].score + " LuceneModel\r\n";
					writer2.write(result);
				}
				

			}
			writer2.close();
			queryReader.close();
			

		} catch (Exception e) {
			System.out.println("Error while querying  : " +e.getMessage());
			e.printStackTrace();
			System.exit(-1);
		}				

	}

	/**
	 * Constructor
	 * 
	 * @param indexDir
	 *            the name of the folder in which the index should be created
	 * @throws java.io.IOException
	 *             when exception creating index.
	 */
	Lucene(String indexDir) throws IOException {

		FSDirectory dir = FSDirectory.open(new File(indexDir));

		IndexWriterConfig config = new IndexWriterConfig(Version.LUCENE_47, sAnalyzer);

		writer = new IndexWriter(dir, config);
	}

	/**
	 * Indexes a file or directory
	 * 
	 * @param fileName
	 *            the name of a text file or a folder we wish to add to the
	 *            index
	 * @throws java.io.IOException
	 *             when exception
	 */
	public void indexFileOrDirectory(String fileName) throws IOException {
		// ===================================================
		// gets the list of files in a folder (if user has submitted
		// the name of a folder) or gets a single file name (is user
		// has submitted only the file name)
		// ===================================================
		addFiles(new File(fileName));

		int originalNumDocs = writer.numDocs();
		for (File f : queue) {
			FileReader fr = null;
			try {
				Document doc = new Document();

				// ===================================================
				// add contents of file
				// ===================================================
				fr = new FileReader(f);
				doc.add(new TextField("contents", fr));
				doc.add(new StringField("path", f.getPath(), Field.Store.YES));
				doc.add(new StringField("filename", f.getName(), Field.Store.YES));
				writer.addDocument(doc);

				System.out.println("Added: " + f);
			} catch (Exception e) {
				System.out.println("Could not add: " + f);
			} finally {
				fr.close();
			}
		}

		int newNumDocs = writer.numDocs();
		System.out.println("");
		System.out.println("************************");
		System.out
		.println((newNumDocs - originalNumDocs) + " documents added.");
		System.out.println("************************");

		queue.clear();
	}

	private void addFiles(File file) {

		if (!file.exists()) {
			System.out.println(file + " does not exist.");
		}
		if (file.isDirectory()) {
			for (File f : file.listFiles()) {
				addFiles(f);
			}
		} else {
			String filename = file.getName().toLowerCase();
			// ===================================================
			// Only index text files
			// ===================================================
			if (filename.endsWith(".htm") || filename.endsWith(".html")
					|| filename.endsWith(".xml") || filename.endsWith(".txt")) {
				queue.add(file);
			} else {
				System.out.println("Skipped " + filename);
			}
		}
	}

	/**
	 * Close the index.
	 * 
	 * @throws java.io.IOException
	 *             when exception closing
	 */
	public void closeIndex() throws IOException {
		writer.close();
	}
}
