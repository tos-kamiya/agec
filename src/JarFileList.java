// reference http://java6.blog117.fc2.com/blog-entry-16.html

import java.io.*;
import java.util.*;
import java.util.jar.*;

public class JarFileList {
	public static void main(String[] args) throws IOException {
		if (args.length == 0) {
			System.err.println("error: no jar file specified");
			System.exit(1);
		}
		String jarFileName = args[0];

		try (JarFile jarFile = new JarFile(new File(jarFileName))) {
            for (JarEntry entry : Collections.list(jarFile.entries()))
				System.out.println(entry.getName());
		}
	}
}

