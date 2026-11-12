Name:		japicmp-gradle-plugin
Version:	0.4.6
Release:	1
Summary:	Gradle plugin for comparing jar APIs
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/melix/japicmp-gradle-plugin
# Commit 33017ed (Release 0.4.6). Upstream tags stop at RELEASE_0_4_5.
# The catalog coordinate is me.champeau.gradle:japicmp-gradle-plugin.
# The Gradle wrapper jar is not in this archive. Sources are compiled
# with javac against the installed Gradle API jars. The Gradle tool is
# not invoked.
Source0:	japicmp-gradle-plugin-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	gradle
BuildRequires:	apache-groovy
BuildRequires:	mvn(javax.inject:javax.inject)
BuildRequires:	mvn(org.javassist:javassist)
BuildRequires:	mvn(com.github.siom79.japicmp:japicmp) = 0.23.1
BuildRequires:	mvn(com.google.guava:guava)
BuildRequires:	mvn(javax.xml.bind:jaxb-api)
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem
Requires:	gradle

%description
me.champeau.gradle:japicmp-gradle-plugin %{version}. Plugin id
me.champeau.gradle.japicmp. JApiCmpWorkerAction compares two jars
through japicmp and writes a text report. The sources are compiled
with javac. The Gradle tool is not invoked.

%prep
%autosetup -n japicmp-gradle-plugin-%{version} -p1
find . -type f \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -print > binaries.list
find . -type d -name '*.jar' -print >> binaries.list
if [ -s binaries.list ]; then
	cat binaries.list
	exit 1
fi
find src/main/java -name '*.java' | sort > sources.list
test "$(wc -l < sources.list)" -eq 33

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
CP=$(find %{_datadir}/gradle -name '*.jar' | sort | paste -sd: -)
for extra in \
	%{_javadir}/apache-groovy.jar \
	%{_javadir}/apache-groovy-templates.jar \
	%{_javadir}/atinject.jar \
	%{_javadir}/javassist.jar \
	%{_javadir}/japicmp.jar \
	%{_javadir}/guava.jar \
	%{_javadir}/javax.xml.bind.jar
do
	test -s "$extra"
	CP="$CP:$extra"
done
mkdir -p classes
javac --release 8 -Xlint:-options -encoding UTF-8 -cp "$CP" -d classes @sources.list
test "$(find classes -name '*.class' | wc -l)" -eq 41
cp -a src/main/resources/. classes/
test -s classes/templates/default.groovy
mkdir -p classes/META-INF/gradle-plugins
printf '%s\n' 'implementation-class=me.champeau.gradle.japicmp.JapicmpPlugin' \
	> classes/META-INF/gradle-plugins/me.champeau.gradle.japicmp.properties
javap -v -classpath classes me.champeau.gradle.japicmp.JapicmpPlugin | grep -F -q 'major version: 52'
javap -v -classpath classes me.champeau.gradle.japicmp.JApiCmpWorkerAction | grep -F -q 'major version: 52'
printf '%s\n' 'Manifest-Version: 1.0' 'Automatic-Module-Name: me.champeau.gradle.japicmp' > manifest.mf
jar cfm japicmp-gradle-plugin.jar manifest.mf -C classes .
jar i japicmp-gradle-plugin.jar
jar tf japicmp-gradle-plugin.jar | grep -F -q 'me/champeau/gradle/japicmp/JapicmpPlugin.class'
jar tf japicmp-gradle-plugin.jar | grep -F -q 'META-INF/gradle-plugins/me.champeau.gradle.japicmp.properties'
jar tf japicmp-gradle-plugin.jar | grep -F -q 'templates/default.groovy'
desc=$(jar --describe-module --file japicmp-gradle-plugin.jar)
printf '%s\n' "$desc" | grep -F -q 'me.champeau.gradle.japicmp'
if printf '%s\n' "$desc" | grep -F -q 'Unable'; then
	printf '%s\n' "$desc"
	exit 1
fi

cat > japicmp-gradle-plugin.pom << END
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>me.champeau.gradle</groupId>
  <artifactId>japicmp-gradle-plugin</artifactId>
  <version>%{version}</version>
  <name>japicmp Gradle plugin</name>
  <description>Gradle plugin that compares two jars with japicmp.</description>
  <url>https://github.com/melix/japicmp-gradle-plugin</url>
  <licenses>
    <license>
      <name>Apache-2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>com.github.siom79.japicmp</groupId>
      <artifactId>japicmp</artifactId>
      <version>0.23.1</version>
    </dependency>
    <dependency>
      <groupId>org.javassist</groupId>
      <artifactId>javassist</artifactId>
      <version>3.33.0-GA</version>
    </dependency>
    <dependency>
      <groupId>org.apache.groovy</groupId>
      <artifactId>groovy</artifactId>
      <version>4.0.33</version>
    </dependency>
    <dependency>
      <groupId>org.apache.groovy</groupId>
      <artifactId>groovy-templates</artifactId>
      <version>4.0.33</version>
    </dependency>
    <dependency>
      <groupId>javax.inject</groupId>
      <artifactId>javax.inject</artifactId>
      <version>1.0.5</version>
    </dependency>
  </dependencies>
</project>
END

%install
set -eo pipefail
sysjar install --buildroot %{buildroot} \
	--artifact japicmp-gradle-plugin.pom:japicmp-gradle-plugin.jar \
	--file-name japicmp-gradle-plugin \
	--filelist .mfiles
idx="%{buildroot}/usr/share/sysjar/index/me.champeau.gradle/japicmp-gradle-plugin.sysjar"
test -s "$idx"
grep -F -q '"version": "%{version}"' "$idx"
grep -F -q '"artifactId": "japicmp-gradle-plugin"' "$idx"
test -s %{buildroot}%{_javadir}/japicmp-gradle-plugin.jar

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
JAR=%{buildroot}%{_javadir}/japicmp-gradle-plugin.jar
test -s "$JAR"
CP=$(find %{_datadir}/gradle -name '*.jar' | sort | paste -sd: -)
CP="$CP:$JAR"
for extra in \
	%{_javadir}/apache-groovy.jar \
	%{_javadir}/apache-groovy-templates.jar \
	%{_javadir}/atinject.jar \
	%{_javadir}/javassist.jar \
	%{_javadir}/japicmp.jar \
	%{_javadir}/guava.jar \
	%{_javadir}/javax.xml.bind.jar
do
	test -s "$extra"
	CP="$CP:$extra"
done
mkdir -p check/oldsrc/sample check/newsrc/sample check/old check/new
cat > check/oldsrc/sample/Hello.java << 'EOF'
package sample;
public class Hello {
	public String hi() { return "hi"; }
	public String keep() { return "keep"; }
}
EOF
cat > check/newsrc/sample/Hello.java << 'EOF'
package sample;
public class Hello {
	public String keep() { return "keep"; }
}
EOF
javac --release 8 -Xlint:-options -d check/old check/oldsrc/sample/Hello.java
javac --release 8 -Xlint:-options -d check/new check/newsrc/sample/Hello.java
jar cf check/old.jar -C check/old sample
jar cf check/new.jar -C check/new sample
cat > check/Smoke.java << 'EOF'
import me.champeau.gradle.japicmp.JApiCmpWorkerAction;
import me.champeau.gradle.japicmp.JapiCmpWorkerConfiguration;

import java.io.File;
import java.nio.file.Files;
import java.util.Collections;
import java.util.List;

public class Smoke {
	public static void main(String[] args) throws Exception {
		List<String> none = Collections.emptyList();
		JapiCmpWorkerConfiguration cfg = new JapiCmpWorkerConfiguration(
			false,
			true,
			none, none, none, none, none, none, none, none, none, none,
			Collections.emptyList(),
			Collections.emptyList(),
			none,
			Collections.emptyList(),
			Collections.emptyList(),
			Collections.singletonList(new JApiCmpWorkerAction.Archive(new File(args[0]), "1")),
			Collections.singletonList(new JApiCmpWorkerAction.Archive(new File(args[1]), "2")),
			false,
			false,
			false,
			false,
			"protected",
			null,
			null,
			null,
			new File(args[2]),
			null,
			false,
			null);
		new JApiCmpWorkerAction(cfg).run();
		byte[] raw = Files.readAllBytes(new File(args[2]).toPath());
		String text = new String(raw);
		String removed = "REMOVED METHOD: PUBLIC(-) java.lang.String hi()";
		if (!text.contains(removed)) {
			System.out.println(text);
			throw new AssertionError(removed);
		}
		System.out.println("japicmp_plugin_ok hi");
	}
}
EOF
javac --release 8 -Xlint:-options -cp "$CP" -d check check/Smoke.java
"$JAVA_HOME/bin/java" -cp "check:$CP" Smoke check/old.jar check/new.jar check/report.txt > check/out.txt
cat check/report.txt
cat check/out.txt
grep -F -q 'REMOVED METHOD: PUBLIC(-) java.lang.String hi()' check/report.txt
grep -F -qx 'japicmp_plugin_ok hi' check/out.txt

%files -f .mfiles
%doc README.adoc
%license LICENSE.txt
