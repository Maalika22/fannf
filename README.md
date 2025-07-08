ySpaceFormProject – Full Featured Local JSP + Servlet Dashboard

> Purpose – A self‑contained web app (runs on local Tomcat 10 +) that lets you navigate, view, edit, bulk‑upload (CSV), delete, and paginate spacecraft records stored in MySQL.

Copy the tree below, paste each file into its place, add the MySQL JDBC JAR to WEB-INF/lib, compile, and run.

📁 Folder structure

SpaceFormProject/
├─ src/
│  └─ com/example/space/
│      ├─ DBUtil.java
│      ├─ SpaceDAO.java
│      ├─ CSVUtil.java
│      └─ SpaceServlet.java
├─ WebContent/
│   ├─ index.jsp
│   ├─ fragments/
│   │   ├─ header.jsp
│   │   └─ footer.jsp
│   ├─ styles/
│   │   └─ style.css
│   ├─ scripts/
│   │   └─ script.js
│   └─ WEB-INF/
│       ├─ web.xml
│       └─ lib/
│           └─ mysql-connector-j-8.x.x.jar
└─ build_and_run.sh   (optional helper script)


---

1  Java source files ( src/com/example/space )

1.1  DBUtil.java

package com.example.space;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

public class DBUtil {
    private static final String URL      = "jdbc:mysql://localhost:3306/spacecraft_db?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC";
    private static final String USER     = "root";              //  ←‑‑ change
    private static final String PASSWORD = "your_mysql_password"; // ←‑‑ change

    public static Connection getConnection() throws SQLException {
        return DriverManager.getConnection(URL, USER, PASSWORD);
    }
}

1.2  SpaceDAO.java

package com.example.space;

import java.sql.*;
import java.util.*;

public class SpaceDAO {

    /* ========= Tiny DTO ========= */
    public static class Craft {
        public int id;
        public String a, b, c;
    }

    /* ========= CRUD ========= */
    public List<Craft> findAll() throws SQLException {
        String sql = "SELECT * FROM spacecraft ORDER BY craft_id";
        try (Connection con = DBUtil.getConnection();
             PreparedStatement ps = con.prepareStatement(sql);
             ResultSet rs = ps.executeQuery()) {

            List<Craft> list = new ArrayList<>();
            while (rs.next()) list.add(rowToCraft(rs));
            return list;
        }
    }

    public List<Craft> findPage(int offset, int limit) throws SQLException {
        String sql = "SELECT * FROM spacecraft ORDER BY craft_id LIMIT ? OFFSET ?";
        try (Connection con = DBUtil.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {
            ps.setInt(1, limit);
            ps.setInt(2, offset);
            ResultSet rs = ps.executeQuery();
            List<Craft> list = new ArrayList<>();
            while (rs.next()) list.add(rowToCraft(rs));
            return list;
        }
    }

    public int count() throws SQLException {
        try (Connection con = DBUtil.getConnection();
             PreparedStatement ps = con.prepareStatement("SELECT COUNT(*) FROM spacecraft");
             ResultSet rs = ps.executeQuery()) {
            return rs.next() ? rs.getInt(1) : 0;
        }
    }

    public Craft findById(int id) throws SQLException {
        String sql = "SELECT * FROM spacecraft WHERE craft_id=?";
        try (Connection con = DBUtil.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {
            ps.setInt(1, id);
            ResultSet rs = ps.executeQuery();
            return rs.next() ? rowToCraft(rs) : null;
        }
    }

    public void save(Craft c) throws SQLException {
        String sql = c.id == 0 ?
            "INSERT INTO spacecraft(param_a,param_b,param_c) VALUES(?,?,?)" :
            "UPDATE spacecraft SET param_a=?,param_b=?,param_c=? WHERE craft_id=?";
        try (Connection con = DBUtil.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {
            ps.setString(1, c.a);
            ps.setString(2, c.b);
            ps.setString(3, c.c);
            if (c.id != 0) ps.setInt(4, c.id);
            ps.executeUpdate();
        }
    }

    public void delete(int id) throws SQLException {
        try (Connection con = DBUtil.getConnection();
             PreparedStatement ps = con.prepareStatement("DELETE FROM spacecraft WHERE craft_id=?")) {
            ps.setInt(1, id);
            ps.executeUpdate();
        }
    }

    /* ========= Bulk CSV ========= */
    public void bulkInsert(List<Craft> list) throws SQLException {
        String sql = "INSERT INTO spacecraft(param_a,param_b,param_c) VALUES (?,?,?)";
        try (Connection con = DBUtil.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {
            for (Craft c : list) {
                ps.setString(1, c.a);
                ps.setString(2, c.b);
                ps.setString(3, c.c);
                ps.addBatch();
            }
            ps.executeBatch();
        }
    }

    /* ========= Helper ========= */
    private Craft rowToCraft(ResultSet rs) throws SQLException {
        Craft c = new Craft();
        c.id = rs.getInt("craft_id");
        c.a  = rs.getString("param_a");
        c.b  = rs.getString("param_b");
        c.c  = rs.getString("param_c");
        return c;
    }
}

1.3  CSVUtil.java

package com.example.space;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

public class CSVUtil {
    /**
     * Very small CSV parser – expects each line: param_a,param_b,param_c (no header).
     */
    public static List<SpaceDAO.Craft> parseCSV(InputStream in) throws IOException {
        List<SpaceDAO.Craft> list = new ArrayList<>();
        try (BufferedReader br = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
            String line;
            while ((line = br.readLine()) != null) {
                String[] parts = line.split(",", -1);
                if (parts.length < 3) continue;   // skip bad lines
                SpaceDAO.Craft c = new SpaceDAO.Craft();
                c.id = 0;                           // new record
                c.a  = parts[0].trim();
                c.b  = parts[1].trim();
                c.c  = parts[2].trim();
                list.add(c);
            }
        }
        return list;
    }
}

1.4  SpaceServlet.java

package com.example.space;

import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.MultipartConfig;
import jakarta.servlet.http.*;
import java.io.IOException;
import java.sql.SQLException;
import java.util.List;

@MultipartConfig(maxFileSize = 5 * 1024 * 1024) // 5 MB
public class SpaceServlet extends HttpServlet {
    private final SpaceDAO dao = new SpaceDAO();

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse res)
            throws ServletException, IOException {
        try {
            // Pagination – one record per page (change pageSize if you like)
            int pageSize = 1;
            int page = 1;
            String pageStr = req.getParameter("page");
            if (pageStr != null && !pageStr.isEmpty()) page = Integer.parseInt(pageStr);

            int total = dao.count();
            int totalPages = (int) Math.ceil(total / (double) pageSize);
            page = Math.max(1, Math.min(page, totalPages));
            int offset = (page - 1) * pageSize;

            List<SpaceDAO.Craft> currentPage = dao.findPage(offset, pageSize);
            SpaceDAO.Craft current = currentPage.isEmpty() ? null : currentPage.get(0);

            // For dropdown navigation we still fetch all IDs (small table)
            req.setAttribute("crafts", dao.findAll());
            req.setAttribute("current", current);
            req.setAttribute("page", page);
            req.setAttribute("totalPages", totalPages);

            req.getRequestDispatcher("/index.jsp").forward(req, res);
        } catch (SQLException e) {
            throw new ServletException(e);
        }
    }

    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse res)
            throws ServletException, IOException {
        try {
            String action = req.getParameter("action");

            if ("save".equals(action)) {
                SpaceDAO.Craft c = new SpaceDAO.Craft();
                String id   = req.getParameter("craft_id");
                c.id        = id == null || id.isEmpty() ? 0 : Integer.parseInt(id);
                c.a         = req.getParameter("param_a");
                c.b         = req.getParameter("param_b");
                c.c         = req.getParameter("param_c");
                dao.save(c);

            } else if ("delete".equals(action)) {
                int id = Integer.parseInt(req.getParameter("craft_id"));
                dao.delete(id);

            } else if ("upload".equals(action)) {
                Part filePart = req.getPart("csvfile");
                if (filePart != null && filePart.getSize() > 0) {
                    List<SpaceDAO.Craft> list = CSVUtil.parseCSV(filePart.getInputStream());
                    dao.bulkInsert(list);
                }
            }

            res.sendRedirect(req.getContextPath() + "/SpaceServlet");
        } catch (SQLException e) {
            throw new ServletException(e);
        }
    }
}


---

2  Deployment descriptor ( WebContent/WEB-INF/web.xml )

<?xml version="1.0" encoding="UTF-8"?>
<web-app xmlns="https://jakarta.ee/xml/ns/jakartaee" version="10">
    <servlet>
        <servlet-name>SpaceServlet</servlet-name>
        <servlet-class>com.example.space.SpaceServlet</servlet-class>
    </servlet>
    <servlet-mapping>
        <servlet-name>SpaceServlet</servlet-name>
        <url-pattern>/SpaceServlet</url-pattern>
    </servlet-mapping>
    <welcome-file-list>
        <welcome-file>SpaceServlet</welcome-file>
    </welcome-file-list>
</web-app>


---

3  JSP front‑end ( WebContent/index.jsp )

<%@ page contentType="text/html; charset=UTF-8" %>
<%@ taglib uri="https://jakarta.ee/jsp/jstl/core" prefix="c" %>
<jsp:include page="fragments/header.jsp"/>

<div class="container">
    <!-- ── Navigation / Upload side bar ─────────────────────────────── -->
    <aside class="nav">
        <h2>Navigate</h2>
        <form method="get" action="SpaceServlet">
            <select name="craft" onchange="this.form.submit()">
                <option value="">-- jump to id --</option>
                <c:forEach var="c" items="${crafts}">
                    <option value="${c.id}" ${current != null && current.id == c.id ? "selected" : ""}>#${c.id}</option>
                </c:forEach>
            </select>
        </form>

        <h2 class="mt">Bulk CSV&nbsp;Upload</h2>
        <form method="post" action="SpaceServlet" enctype="multipart/form-data">
            <input type="file" name="csvfile" accept=".csv" required />
            <button class="upload" type="submit" name="action" value="upload">⇪ Upload</button>
        </form>
    </aside>

    <!-- ── Main editor card ─────────────────────────────────────────── -->
    <main class="card">
        <c:choose>
            <c:when test="${current != null}">
                <form method="post" action="SpaceServlet">
                    <input type="hidden" name="craft_id" value="${current.id}" />

                    <label>Parameter&nbsp;A</label>
                    <input type="text" name="param_a" value="${current.a}" required />

                    <label>Parameter&nbsp;B</label>
                    <input type="text" name="param_b" value="${current.b}" required />

                    <label>Parameter&nbsp;C</label>
                    <input type="text" name="param_c" value="${current.c}" required />

                    <div class="btn-group">
                        <button type="submit" name="action" value="save">💾 Save</button>
                        <button type="submit" name="action" value="delete" class="danger" onclick="return confirm('Delete this record?');">🗑 Delete</button>
                    </div>
                </form>
            </c:when>
            <c:otherwise>
                <p class="placeholder">No records yet – upload a CSV or add one.</p>
                <form method="post" action="SpaceServlet">
                    <input type="hidden" name="craft_id" value="" />
                    <button class="new" type="submit" name="action" value="save">➕ New Record</button>
                </form>
            </c:otherwise>
        </c:choose>

        <!-- Pagination bar -->
        <c:if test="${totalPages > 1}">
            <nav class="pagination">
                <c:if test="${page > 1}"><a href="SpaceServlet?page=${page-1}">« Prev</a></c:if>
                <span>Page ${page} / ${totalPages}</span>
                <c:if test="${page < totalPages}"><a href="SpaceServlet?page=${page+1}">Next »</a></c:if>
            </nav>
        </c:if>
    </main>
</div>

<jsp:include page="fragments/footer.jsp"/>

3.1  fragments/header.jsp

<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8" />
    <title>Spacecraft Dashboard</title>
    <link rel="stylesheet" href="styles/style.css" />
    <script src="scripts/script.js" defer></script>
</head>
<body>

3.2  fragments/footer.jsp

</body>
</html>


---

4  Static assets

4.1  WebContent/styles/style.css

/* ── Colourful neon‑retro skin ───────────────────────────────────── */
:root{
    --bg: #0f172a;
    --fg: #f8fafc;
    --primary: #38bdf8;
    --secondary: #a855f7;
    --danger: #f87171;
    --surface: #1e293b;
    --surface-alt: #334155;
}
*{box-sizing:border-box;}
body{margin:0;font-family:"Trebuchet MS",sans-serif;background:var(--bg);color:var(--fg);}

h2{margin:1rem 0 0.3rem;font-size:1rem;color:var(--secondary);text-transform:uppercase;letter-spacing:1px;}
.mt{margin-top:2rem;}

.container{display:grid;grid-template-columns:220px 1fr;height:100vh;}

/* Navigation bar */
.nav{padding:1.2rem;background:linear-gradient(180deg,var(--surface),var(--surface-alt));box-shadow:2px 0 6px rgba(0,0,0,.4);overflow:auto;}
.nav select{width:100%;padding:0.5rem;border:none;border-radius:6px;background:var(--surface-alt);color:var(--fg);}
.nav button.upload{margin-top:0.6rem;width:100%;}

/* Main editable card */
.card{margin:2rem;display:flex;flex-direction:column;gap:0.8rem;padding:2rem 3rem;background:var(--surface);border-radius:14px;box-shadow:0 6px 16px rgba(0,0,0,.35);}
.card label{font-size:0.85rem;color:var(--primary);}
.card input{padding:0.55rem 0.8rem;border:none;border-radius:8px;background:var(--surface-alt);color:var(--fg);}

.btn-group{display:flex;gap:1rem;margin-top:1rem;}
button{cursor:pointer;padding:0.7rem 1.4rem;border:none;border-radius:8px;font-weight:bold;font-size:0.9rem;background:var(--primary);color:var(--bg);transition:transform .15s ease,background .15s ease;}
button:hover{transform:translateY(-2px);}button:active{transform:scale(.97);}
button.danger{background:var(--danger);}button.new{background:var(--secondary);}

/* Pagination */
.pagination{margin-top:1.6rem;display:flex;justify-content:center;align-items:center;gap:1rem;font-size:0.9rem;}
.pagination a{color:var(--primary);text-decoration:none;border:1px solid var(--primary);padding:0.3rem 0.6rem;border-radius:4px;}
.pagination a:hover{background:var(--primary);color:var(--bg);}
.placeholder{opacity:.6;}

4.2  WebContent/scripts/script.js

// Tiny helper to show the chosen CSV file name in the upload button label (optional flair)
document.addEventListener("DOMContentLoaded",() => {
  const fileInput = document.querySelector('input[type="file"][name="csvfile"]');
  if(!fileInput) return;
  fileInput.addEventListener('change', () => {
    if(fileInput.files.length){
      fileInput.nextElementSibling.textContent = `⇪ Upload (${fileInput.files[0].name})`;
    }
  });
});


---

5  Optional helper – build_and_run.sh

#!/usr/bin/env bash
# Compile Java then copy to Tomcat webapps (adjust TOMCAT_HOME) 
TOMCAT_HOME="$HOME/apache-tomcat-10.1.24"  # change
JAR="$TOMCAT_HOME/lib/servlet-api.jar"
MYSQL_JAR="WebContent/WEB-INF/lib/mysql-connector-j-8.x.x.jar"

mkdir -p WebContent/WEB-INF/classes
javac -cp "$JAR:$MYSQL_JAR" \
  -d WebContent/WEB-INF/classes src/com/example/space/*.java || exit 1

# explode into webapps for hot reload
rm -rf "$TOMCAT_HOME/webapps/SpaceFormProject"
cp -r WebContent "$TOMCAT_HOME/webapps/SpaceFormProject"
$TOMCAT_HOME/bin/startup.sh


---

🔗 Running steps (quick recap)

1. Create spacecraft_db table (see previous reply) and update DB credentials in DBUtil.java.


2. Drop MySQL driver JAR into WebContent/WEB-INF/lib/.


3. Compile Java ⇒ copy classes into WEB-INF/classes (script above or VS Code "Run on Tomcat").


4. Start Tomcat and visit http://localhost:8080/SpaceFormProject/.



Enjoy a colourful dashboard with dropdown navigation, CSV bulk‑upload, edit/save/delete, and per‑record pagination – all 100 % local, no external CDNs.



I’ve placed the full project tree and source code—complete with CSV upload, per-record pagination, colourful UI, and all required JSP/Servlet logic—into the canvas on the right. Copy each file into the matching folder names, adjust your MySQL credentials in DBUtil.java, add the JDBC driver JAR, compile, and run on your local Tomcat.

Let me know whenever you’d like tweaks (e.g., more parameters, extra validation, embedded Tomcat launcher, etc.) and we can iterate right inside the canvas. Happy building!







SpaceFormProject – Complete Source (Enhanced UI)

Below is 100 % of the code for every file in the structure you specified. Copy each snippet into the matching path and you can compile/run locally on Tomcat 10+ with no internet.

> Features

10 parameters per spacecraft (name, subsystem, orbit_type, status, launch_date, mass_kg, power_kw, fuel_level_pct, altitude_km, velocity_km_s)

Fully center-aligned neon UI, two-column grid

Navigation dropdown, per-record pagination, fixed Save/Delete/New row

CSV bulk upload (no header required, 10 columns)

All code uses Jakarta Servlet 10, JSTL 3, MySQL JDBC 8





---

📁 Folder structure

SpaceFormProject/
├─ src/com/example/space/
│   ├─ DBUtil.java
│   ├─ SpaceDAO.java
│   ├─ CSVUtil.java
│   └─ SpaceServlet.java
├─ WebContent/
│   ├─ index.jsp
│   ├─ fragments/
│   │   ├─ header.jsp
│   │   └─ footer.jsp
│   ├─ styles/style.css
│   ├─ scripts/script.js
│   └─ WEB-INF/
│       ├─ web.xml
│       └─ lib/
│           ├─ mysql-connector-j-8.x.x.jar
│           ├─ jakarta.servlet.jsp.jstl-api-3.0.1.jar
│           └─ jakarta.servlet.jsp.jstl-3.0.1.jar
└─ build_and_run.sh  (optional helper)


---

1  Java source – src/com/example/space/

1.1  DBUtil.java

package com.example.space;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

/** Simple helper to get a JDBC connection */
public class DBUtil {
    private static final String URL  = "jdbc:mysql://localhost:3306/spacecraft_db?useSSL=false&serverTimezone=UTC";
    private static final String USER = "root";              // <<— change
    private static final String PASS = "your_password";      // <<— change

    public static Connection getConnection() throws SQLException {
        return DriverManager.getConnection(URL, USER, PASS);
    }
}

1.2  SpaceDAO.java

package com.example.space;

import java.sql.*;
import java.util.*;

/** DAO layer encapsulating CRUD + pagination + bulk insert */
public class SpaceDAO {

    /* ───────────────── DTO ───────────────── */
    public static class Craft {
        public int id;
        public String name, subsystem, orbitType, status, launchDate;
        public String massKg, powerKw, fuelPct, altitudeKm, velocityKmS;
    }

    /* ───────────────── Helpers ───────────────── */
    private Craft row(ResultSet rs) throws SQLException {
        Craft c = new Craft();
        c.id           = rs.getInt("craft_id");
        c.name         = rs.getString("name");
        c.subsystem    = rs.getString("subsystem");
        c.orbitType    = rs.getString("orbit_type");
        c.status       = rs.getString("status");
        c.launchDate   = rs.getString("launch_date");
        c.massKg       = rs.getString("mass_kg");
        c.powerKw      = rs.getString("power_kw");
        c.fuelPct      = rs.getString("fuel_level_pct");
        c.altitudeKm   = rs.getString("altitude_km");
        c.velocityKmS  = rs.getString("velocity_km_s");
        return c;
    }

    /* ───────────────── Pagination ───────────────── */
    public List<Craft> findPage(int offset, int limit) throws SQLException {
        String sql = "SELECT * FROM spacecraft ORDER BY craft_id LIMIT ? OFFSET ?";
        try (Connection con = DBUtil.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {
            ps.setInt(1, limit);
            ps.setInt(2, offset);
            ResultSet rs = ps.executeQuery();
            List<Craft> list = new ArrayList<>();
            while (rs.next()) list.add(row(rs));
            return list;
        }
    }

    public int count() throws SQLException {
        try (Connection con = DBUtil.getConnection();
             PreparedStatement ps = con.prepareStatement("SELECT COUNT(*) FROM spacecraft");
             ResultSet rs = ps.executeQuery()) {
            return rs.next() ? rs.getInt(1) : 0;
        }
    }

    /* ───────────────── Dropdown IDs ───────────────── */
    public List<Integer> allIds() throws SQLException {
        try (Connection con = DBUtil.getConnection();
             PreparedStatement ps = con.prepareStatement("SELECT craft_id FROM spacecraft ORDER BY craft_id");
             ResultSet rs = ps.executeQuery()) {
            List<Integer> ids = new ArrayList<>();
            while (rs.next()) ids.add(rs.getInt(1));
            return ids;
        }
    }

    /* ───────────────── Save / Delete ───────────────── */
    public void save(Craft c) throws SQLException {
        String sql = c.id == 0 ?
            "INSERT INTO spacecraft(name,subsystem,orbit_type,status,launch_date,mass_kg,power_kw,fuel_level_pct,altitude_km,velocity_km_s) VALUES (?,?,?,?,?,?,?,?,?,?)" :
            "UPDATE spacecraft SET name=?,subsystem=?,orbit_type=?,status=?,launch_date=?,mass_kg=?,power_kw=?,fuel_level_pct=?,altitude_km=?,velocity_km_s=? WHERE craft_id=?";
        try (Connection con = DBUtil.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {
            int i = 1;
            ps.setString(i++, c.name);
            ps.setString(i++, c.subsystem);
            ps.setString(i++, c.orbitType);
            ps.setString(i++, c.status);
            ps.setString(i++, c.launchDate);
            ps.setString(i++, c.massKg);
            ps.setString(i++, c.powerKw);
            ps.setString(i++, c.fuelPct);
            ps.setString(i++, c.altitudeKm);
            ps.setString(i++, c.velocityKmS);
            if (c.id != 0) ps.setInt(i, c.id);
            ps.executeUpdate();
        }
    }

    public void delete(int id) throws SQLException {
        try (Connection con = DBUtil.getConnection();
             PreparedStatement ps = con.prepareStatement("DELETE FROM spacecraft WHERE craft_id=?")) {
            ps.setInt(1, id);
            ps.executeUpdate();
        }
    }

    /* ───────────────── Bulk CSV ───────────────── */
    public void bulkInsert(List<Craft> list) throws SQLException {
        String sql = "INSERT INTO spacecraft(name,subsystem,orbit_type,status,launch_date,mass_kg,power_kw,fuel_level_pct,altitude_km,velocity_km_s) VALUES (?,?,?,?,?,?,?,?,?,?)";
        try (Connection con = DBUtil.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {
            for (Craft c : list) {
                int i = 1;
                ps.setString(i++, c.name);
                ps.setString(i++, c.subsystem);
                ps.setString(i++, c.orbitType);
                ps.setString(i++, c.status);
                ps.setString(i++, c.launchDate);
                ps.setString(i++, c.massKg);
                ps.setString(i++, c.powerKw);
                ps.setString(i++, c.fuelPct);
                ps.setString(i++, c.altitudeKm);
                ps.setString(i++, c.velocityKmS);
                ps.addBatch();
            }
            ps.executeBatch();
        }
    }
}

1.3  CSVUtil.java

package com.example.space;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Tiny CSV parser (10 columns, no header) */
public class CSVUtil {
    public static List<SpaceDAO.Craft> parse(InputStream in) throws IOException {
        List<SpaceDAO.Craft> list = new ArrayList<>();
        try (BufferedReader br = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
            String ln;
            while ((ln = br.readLine()) != null) {
                if (ln.isBlank()) continue;
                String[] p = ln.split(",", -1);
                if (p.length < 10) continue;      // skip bad lines
                SpaceDAO.Craft c = new SpaceDAO.Craft();
                c.name=p[0]; c.subsystem=p[1]; c.orbitType=p[2]; c.status=p[3];
                c.launchDate=p[4]; c.massKg=p[5]; c.powerKw=p[6]; c.fuelPct=p[7];
                c.altitudeKm=p[8]; c.velocityKmS=p[9];
                list.add(c);
            }
        }
        return list;
    }
}

1.4  SpaceServlet.java

package com.example.space;

import jakarta.servlet.annotation.MultipartConfig;
import jakarta.servlet.http.*;
import jakarta.servlet.*;
import java.io.IOException;
import java.sql.SQLException;
import java.util.List;

@MultipartConfig(maxFileSize = 5*1024*1024)
public class SpaceServlet extends HttpServlet {
    private final SpaceDAO dao = new SpaceDAO();
    private static final int PAGE_SIZE = 1;   // one record per page

    @Override protected void doGet(HttpServletRequest rq, HttpServletResponse rs) throws ServletException, IOException {
        try {
            int page = 1;
            String ps = rq.getParameter("page");
            if (ps != null && !ps.isBlank()) page = Integer.parseInt(ps);
            int total = dao.count();
            int totalPages = Math.max(1, (int)Math.ceil(total/(double)PAGE_SIZE));
            page = Math.max(1, Math.min(page, totalPages));
            int offset = (page-1)*PAGE_SIZE;

            List<SpaceDAO.Craft> currentPage = dao.findPage(offset, PAGE_SIZE);
            SpaceDAO.Craft current = currentPage.isEmpty() ? null : currentPage.get(0);

            rq.setAttribute("ids", dao.allIds());
            rq.setAttribute("current", current);
            rq.setAttribute("page", page);
            rq.setAttribute("totalPages", totalPages);
            rq.getRequestDispatcher("/index.jsp").forward(rq, rs);
        } catch (SQLException e) {
            throw new ServletException(e);
        }
    }

    @Override protected void doPost(HttpServletRequest rq, HttpServletResponse rs) throws ServletException, IOException {
        try {
            String action = rq.getParameter("action");
            if ("save".equals(action)) {
                SpaceDAO.Craft c = new SpaceDAO.Craft();
                String idStr = rq.getParameter("craft_id");
                c.id = (idStr==null||idStr.isBlank()) ? 0 : Integer.parseInt(idStr);
                c.name = rq.getParameter("name");
                c.subsystem = rq.getParameter("subsystem");
                c.orbitType = rq.getParameter("orbit_type");
                c.status = rq.getParameter("status");
                c.launchDate = rq.getParameter("launch_date");
                c.massKg = rq.getParameter("mass_kg");
                c.powerKw = rq.getParameter("power_kw");
                c.fuelPct = rq.getParameter("fuel_level_pct");
                c.altitudeKm = rq.getParameter("altitude_km");
                c.velocityKmS = rq.getParameter("velocity_km_s");
                dao.save(c);

            } else if ("delete".equals(action)) {
                int id = Integer.parseInt(rq.getParameter("craft_id"));
                dao.delete(id);

            } else if ("upload".equals(action)) {
                Part file = rq.getPart("csvfile");
                if (file != null && file.getSize()>0) {
                    List<SpaceDAO.Craft> list = CSVUtil.parse(file.getInputStream());
                    dao.bulkInsert(list);
                }
            }
            rs.sendRedirect(rq.getContextPath() + "/SpaceServlet");
        } catch (SQLException e) {
            throw new ServletException(e);
        }
    }
}


---

2  Web descriptor – WebContent/WEB-INF/web.xml

<?xml version="1.0" encoding="UTF-8"?>
<web-app xmlns="https://jakarta.ee/xml/ns/jakartaee" version="10">
    <servlet>
        <servlet-name>SpaceServlet</servlet-name>
        <servlet-class>com.example.space.SpaceServlet</servlet-class>
    </servlet>
    <servlet-mapping>
        <servlet-name>SpaceServlet</servlet-name>
        <url-pattern>/SpaceServlet</url-pattern>
    </servlet-mapping>
    <welcome-file-list>
        <welcome-file>SpaceServlet</welcome-file>
    </welcome-file-list>
</web-app>


---

3  JSP views – WebContent/

3.1  fragments/header.jsp

<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8" />
    <title>Spacecraft Dashboard</title>
    <link rel="stylesheet" href="styles/style.css" />
    <script src="scripts/script.js" defer></script>
</head>
<body>

3.2  fragments/footer.jsp

</body>
</html>

3.3  index.jsp

<%@ page contentType="text/html; charset=UTF-8" %>
<%@ taglib uri="https://jakarta.ee/jsp/jstl/core" prefix="c" %>
<jsp:include page="fragments/header.jsp"/>

<div class="outer">
  <aside class="nav">
    <h2>Jump to ID</h2>
    <form method="get" action="SpaceServlet">
      <select name="page" onchange="this.form.submit()">
        <c:forEach var="id" items="${ids}" varStatus="st">
          <option value="${st.index+1}" ${st.index+1==page?"selected":""}>#${id}</option>
        </c:forEach>
      </select>
    </form>

    <h2 class="mt">Bulk CSV</h2>
    <form method="post" action="SpaceServlet" enctype="multipart/form-data">
      <input type="file" name="csvfile" accept=".csv" required />
      <button class="upload" type="submit" name="action" value="upload">⇪ Upload</button>
    </form>
  </aside>

  <main class="card">
    <c:choose>
      <c:when test="${current!=null}">
        <form method="post" action="SpaceServlet">
          <input type="hidden" name="craft_id" value="${current.id}" />

          <div class="grid">
            <label>Name <input type="text" name="name" value="${current.name}" required /></label>
            <label>Subsystem <input type="text" name="subsystem" value="${current.subsystem}" required /></label>
            <label>Orbit Type <input type="text" name="orbit_type" value="${current.orbitType}" required /></label>
            <label>Status <input type="text" name="status" value="${current.status}" required /></label>
            <label>Launch Date <input type="date" name="launch_date" value="${current.launchDate}" /></label>
            <label>Mass (kg) <input type="number" name="mass_kg" value="${current.massKg}" step="0.1" /></label>
            <label>Power (kW) <input type="number" name="power_kw" value="${current.powerKw}" step="0.1" /></label>
            <label>Fuel (%) <input type="number" name="fuel_level_pct" value="${current.fuelPct}" /></label>
            <label>Altitude (km) <input type="number" name="altitude_km" value="${current.altitudeKm}" step="0.1" /></label>
            <label>Velocity (km/s) <input type="number" name="velocity_km_s" value="${current.velocityKmS}" step="0.01" /></label>
          </div>

          <div class="btn-row">
            <button type="




            SpaceFormProject – Complete Source (Enhanced UI)

Below is 100 % of the code for every file in the structure you specified. Copy each snippet into the matching path and you can compile/run locally on Tomcat 10+ with no internet.

> Features

10 parameters per spacecraft (name, subsystem, orbit_type, status, launch_date, mass_kg, power_kw, fuel_level_pct, altitude_km, velocity_km_s)

Fully center-aligned neon UI, two-column grid

Navigation dropdown, per-record pagination, fixed Save/Delete/New row

CSV bulk upload (no header required, 10 columns)

All code uses Jakarta Servlet 10, JSTL 3, MySQL JDBC 8





---

📁 Folder structure

SpaceFormProject/
├─ src/com/example/space/
│   ├─ DBUtil.java
│   ├─ SpaceDAO.java
│   ├─ CSVUtil.java
│   └─ SpaceServlet.java
├─ WebContent/
│   ├─ index.jsp
│   ├─ fragments/
│   │   ├─ header.jsp
│   │   └─ footer.jsp
│   ├─ styles/style.css
│   ├─ scripts/script.js
│   └─ WEB-INF/
│       ├─ web.xml
│       └─ lib/
│           ├─ mysql-connector-j-8.x.x.jar
│           ├─ jakarta.servlet.jsp.jstl-api-3.0.1.jar
│           └─ jakarta.servlet.jsp.jstl-3.0.1.jar
└─ build_and_run.sh  (optional helper)


---

1  Java source – src/com/example/space/

1.1  DBUtil.java

package com.example.space;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

/** Simple helper to get a JDBC connection */
public class DBUtil {
    private static final String URL  = "jdbc:mysql://localhost:3306/spacecraft_db?useSSL=false&serverTimezone=UTC";
    private static final String USER = "root";              // <<— change
    private static final String PASS = "your_password";      // <<— change

    public static Connection getConnection() throws SQLException {
        return DriverManager.getConnection(URL, USER, PASS);
    }
}

1.2  SpaceDAO.java

package com.example.space;

import java.sql.*;
import java.util.*;

/** DAO layer encapsulating CRUD + pagination + bulk insert */
public class SpaceDAO {

    /* ───────────────── DTO ───────────────── */
    public static class Craft {
        public int id;
        public String name, subsystem, orbitType, status, launchDate;
        public String massKg, powerKw, fuelPct, altitudeKm, velocityKmS;
    }

    /* ───────────────── Helpers ───────────────── */
    private Craft row(ResultSet rs) throws SQLException {
        Craft c = new Craft();
        c.id           = rs.getInt("craft_id");
        c.name         = rs.getString("name");
        c.subsystem    = rs.getString("subsystem");
        c.orbitType    = rs.getString("orbit_type");
        c.status       = rs.getString("status");
        c.launchDate   = rs.getString("launch_date");
        c.massKg       = rs.getString("mass_kg");
        c.powerKw      = rs.getString("power_kw");
        c.fuelPct      = rs.getString("fuel_level_pct");
        c.altitudeKm   = rs.getString("altitude_km");
        c.velocityKmS  = rs.getString("velocity_km_s");
        return c;
    }

    /* ───────────────── Pagination ───────────────── */
    public List<Craft> findPage(int offset, int limit) throws SQLException {
        String sql = "SELECT * FROM spacecraft ORDER BY craft_id LIMIT ? OFFSET ?";
        try (Connection con = DBUtil.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {
            ps.setInt(1, limit);
            ps.setInt(2, offset);
            ResultSet rs = ps.executeQuery();
            List<Craft> list = new ArrayList<>();
            while (rs.next()) list.add(row(rs));
            return list;
        }
    }

    public int count() throws SQLException {
        try (Connection con = DBUtil.getConnection();
             PreparedStatement ps = con.prepareStatement("SELECT COUNT(*) FROM spacecraft");
             ResultSet rs = ps.executeQuery()) {
            return rs.next() ? rs.getInt(1) : 0;
        }
    }

    /* ───────────────── Dropdown IDs ───────────────── */
    public List<Integer> allIds() throws SQLException {
        try (Connection con = DBUtil.getConnection();
             PreparedStatement ps = con.prepareStatement("SELECT craft_id FROM spacecraft ORDER BY craft_id");
             ResultSet rs = ps.executeQuery()) {
            List<Integer> ids = new ArrayList<>();
            while (rs.next()) ids.add(rs.getInt(1));
            return ids;
        }
    }

    /* ───────────────── Save / Delete ───────────────── */
    public void save(Craft c) throws SQLException {
        String sql = c.id == 0 ?
            "INSERT INTO spacecraft(name,subsystem,orbit_type,status,launch_date,mass_kg,power_kw,fuel_level_pct,altitude_km,velocity_km_s) VALUES (?,?,?,?,?,?,?,?,?,?)" :
            "UPDATE spacecraft SET name=?,subsystem=?,orbit_type=?,status=?,launch_date=?,mass_kg=?,power_kw=?,fuel_level_pct=?,altitude_km=?,velocity_km_s=? WHERE craft_id=?";
        try (Connection con = DBUtil.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {
            int i = 1;
            ps.setString(i++, c.name);
            ps.setString(i++, c.subsystem);
            ps.setString(i++, c.orbitType);
            ps.setString(i++, c.status);
            ps.setString(i++, c.launchDate);
            ps.setString(i++, c.massKg);
            ps.setString(i++, c.powerKw);
            ps.setString(i++, c.fuelPct);
            ps.setString(i++, c.altitudeKm);
            ps.setString(i++, c.velocityKmS);
            if (c.id != 0) ps.setInt(i, c.id);
            ps.executeUpdate();
        }
    }

    public void delete(int id) throws SQLException {
        try (Connection con = DBUtil.getConnection();
             PreparedStatement ps = con.prepareStatement("DELETE FROM spacecraft WHERE craft_id=?")) {
            ps.setInt(1, id);
            ps.executeUpdate();
        }
    }

    /* ───────────────── Bulk CSV ───────────────── */
    public void bulkInsert(List<Craft> list) throws SQLException {
        String sql = "INSERT INTO spacecraft(name,subsystem,orbit_type,status,launch_date,mass_kg,power_kw,fuel_level_pct,altitude_km,velocity_km_s) VALUES (?,?,?,?,?,?,?,?,?,?)";
        try (Connection con = DBUtil.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {
            for (Craft c : list) {
                int i = 1;
                ps.setString(i++, c.name);
                ps.setString(i++, c.subsystem);
                ps.setString(i++, c.orbitType);
                ps.setString(i++, c.status);
                ps.setString(i++, c.launchDate);
                ps.setString(i++, c.massKg);
                ps.setString(i++, c.powerKw);
                ps.setString(i++, c.fuelPct);
                ps.setString(i++, c.altitudeKm);
                ps.setString(i++, c.velocityKmS);
                ps.addBatch();
            }
            ps.executeBatch();
        }
    }
}

1.3  CSVUtil.java

package com.example.space;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Tiny CSV parser (10 columns, no header) */
public class CSVUtil {
    public static List<SpaceDAO.Craft> parse(InputStream in) throws IOException {
        List<SpaceDAO.Craft> list = new ArrayList<>();
        try (BufferedReader br = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
            String ln;
            while ((ln = br.readLine()) != null) {
                if (ln.isBlank()) continue;
                String[] p = ln.split(",", -1);
                if (p.length < 10) continue;      // skip bad lines
                SpaceDAO.Craft c = new SpaceDAO.Craft();
                c.name=p[0]; c.subsystem=p[1]; c.orbitType=p[2]; c.status=p[3];
                c.launchDate=p[4]; c.massKg=p[5]; c.powerKw=p[6]; c.fuelPct=p[7];
                c.altitudeKm=p[8]; c.velocityKmS=p[9];
                list.add(c);
            }
        }
        return list;
    }
}

1.4  SpaceServlet.java

package com.example.space;

import jakarta.servlet.annotation.MultipartConfig;
import jakarta.servlet.http.*;
import jakarta.servlet.*;
import java.io.IOException;
import java.sql.SQLException;
import java.util.List;

@MultipartConfig(maxFileSize = 5*1024*1024)
public class SpaceServlet extends HttpServlet {
    private final SpaceDAO dao = new SpaceDAO();
    private static final int PAGE_SIZE = 1;   // one record per page

    @Override protected void doGet(HttpServletRequest rq, HttpServletResponse rs) throws ServletException, IOException {
        try {
            int page = 1;
            String ps = rq.getParameter("page");
            if (ps != null && !ps.isBlank()) page = Integer.parseInt(ps);
            int total = dao.count();
            int totalPages = Math.max(1, (int)Math.ceil(total/(double)PAGE_SIZE));
            page = Math.max(1, Math.min(page, totalPages));
            int offset = (page-1)*PAGE_SIZE;

            List<SpaceDAO.Craft> currentPage = dao.findPage(offset, PAGE_SIZE);
            SpaceDAO.Craft current = currentPage.isEmpty() ? null : currentPage.get(0);

            rq.setAttribute("ids", dao.allIds());
            rq.setAttribute("current", current);
            rq.setAttribute("page", page);
            rq.setAttribute("totalPages", totalPages);
            rq.getRequestDispatcher("/index.jsp").forward(rq, rs);
        } catch (SQLException e) {
            throw new ServletException(e);
        }
    }

    @Override protected void doPost(HttpServletRequest rq, HttpServletResponse rs) throws ServletException, IOException {
        try {
            String action = rq.getParameter("action");
            if ("save".equals(action)) {
                SpaceDAO.Craft c = new SpaceDAO.Craft();
                String idStr = rq.getParameter("craft_id");
                c.id = (idStr==null||idStr.isBlank()) ? 0 : Integer.parseInt(idStr);
                c.name = rq.getParameter("name");
                c.subsystem = rq.getParameter("subsystem");
                c.orbitType = rq.getParameter("orbit_type");
                c.status = rq.getParameter("status");
                c.launchDate = rq.getParameter("launch_date");
                c.massKg = rq.getParameter("mass_kg");
                c.powerKw = rq.getParameter("power_kw");
                c.fuelPct = rq.getParameter("fuel_level_pct");
                c.altitudeKm = rq.getParameter("altitude_km");
                c.velocityKmS = rq.getParameter("velocity_km_s");
                dao.save(c);

            } else if ("delete".equals(action)) {
                int id = Integer.parseInt(rq.getParameter("craft_id"));
                dao.delete(id);

            } else if ("upload".equals(action)) {
                Part file = rq.getPart("csvfile");
                if (file != null && file.getSize()>0) {
                    List<SpaceDAO.Craft> list = CSVUtil.parse(file.getInputStream());
                    dao.bulkInsert(list);
                }
            }
            rs.sendRedirect(rq.getContextPath() + "/SpaceServlet");
        } catch (SQLException e) {
            throw new ServletException(e);
        }
    }
}


---

2  Web descriptor – WebContent/WEB-INF/web.xml

<?xml version="1.0" encoding="UTF-8"?>
<web-app xmlns="https://jakarta.ee/xml/ns/jakartaee" version="10">
    <servlet>
        <servlet-name>SpaceServlet</servlet-name>
        <servlet-class>com.example.space.SpaceServlet</servlet-class>
    </servlet>
    <servlet-mapping>
        <servlet-name>SpaceServlet</servlet-name>
        <url-pattern>/SpaceServlet</url-pattern>
    </servlet-mapping>
    <welcome-file-list>
        <welcome-file>SpaceServlet</welcome-file>
    </welcome-file-list>
</web-app>


---

3  JSP views – WebContent/

3.1  fragments/header.jsp

<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8" />
    <title>Spacecraft Dashboard</title>
    <link rel="stylesheet" href="styles/style.css" />
    <script src="scripts/script.js" defer></script>
</head>
<body>

3.2  fragments/footer.jsp

</body>
</html>

3.3  index.jsp

<%@ page contentType="text/html; charset=UTF-8" %>
<%@ taglib uri="https://jakarta.ee/jsp/jstl/core" prefix="c" %>
<jsp:include page="fragments/header.jsp"/>

<div class="outer">
  <aside class="nav">
    <h2>Jump to ID</h2>
    <form method="get" action="SpaceServlet">
      <select name="page" onchange="this.form.submit()">
        <c:forEach var="id" items="${ids}" varStatus="st">
          <option value="${st.index+1}" ${st.index+1==page?"selected":""}>#${id}</option>
        </c:forEach>
      </select>
    </form>

    <h2 class="mt">Bulk CSV</h2>
    <form method="post" action="SpaceServlet" enctype="multipart/form-data">
      <input type="file" name="csvfile" accept=".csv" required />
      <button class="upload" type="submit" name="action" value="upload">⇪ Upload</button>
    </form>
  </aside>

  <main class="card">
    <c:choose>
      <c:when test="${current!=null}">
        <form method="post" action="SpaceServlet">
          <input type="hidden" name="craft_id" value="${current.id}" />

          <div class="grid">
            <label>Name <input type="text" name="name" value="${current.name}" required /></label>
            <label>Subsystem <input type="text" name="subsystem" value="${current.subsystem}" required /></label>
            <label>Orbit Type <input type="text" name="orbit_type" value="${current.orbitType}" required /></label>
            <label>Status <input type="text" name="status" value="${current.status}" required /></label>
            <label>Launch Date <input type="date" name="launch_date" value="${current.launchDate}" /></label>
            <label>Mass (kg) <input type="number" name="mass_kg" value="${current.massKg}" step="0.1" /></label>
            <label>Power (kW) <input type="number" name="power_kw" value="${current.powerKw}" step="0.1" /></label>
            <label>Fuel (%) <input type="number" name="fuel_level_pct" value="${current.fuelPct}" /></label>
            <label>Altitude (km) <input type="number" name="altitude_km" value="${current.altitudeKm}" step="0.1" /></label>
            <label>Velocity (km/s) <input type="number" name="velocity_km_s" value="${current.velocityKmS}" step="0.01" /></label>
          </div>

          <div class="btn-row">
            <button type="

