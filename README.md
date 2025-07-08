SpaceFormProject – Full Featured Local JSP + Servlet Dashboard

> Purpose – A self‑contained web app (runs on local Tomcat 10 +) that lets you navigate, view, edit, bulk‑upload (CSV), delete, and paginate spacecraft records stored in MySQL.

Copy the tree below, paste each file into its place, add the MySQL JDBC JAR to WEB-INF/lib, compile, and run.




---

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

