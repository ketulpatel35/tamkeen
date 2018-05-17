# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    RTL Code
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'SpagoBI Single Sign On',
    'version': '1.0.0',
    'category': 'Integration',
    'description': """
    Odoo 10.0 Integration with SpagoBI Web Application.

    Features:-
    1. On this module we can Configure SpagoBI web application.
        2. SpagoBI Web App configuration steps:-
            1. Login by Odoo administrator account.
            2. Click on Top navigation Setting menu and Activate the
            developer mode.
            3. Odoo setting dashboard on left navigation.
                Click on SpagoBI Web Application -> SpagoBI Web Application.
            4. Type SpagoBI server URL on URL field, add postgres database
            name, add postgres host ip,
               add postgres port, add postgres user name, add postgres
               password, add spagobi admin user name,
               add postgres admin password and click on save button.
            5. After installing this module click on Top navigation menu
            "SpagoBI" menu.
        3. SpagoBI Web App menu name and sequence change steps:-
            1. Login by Odoo administrator account.
            2. Click on Top navigation Setting menu.
            3. Odoo setting dashboard on left navigation.
                Click on Technical -> User Interface -> Menu Items.
            4. Find SpagoBI menu item.
            5. Click on SpagoBI menu item.
            6. Menu item dashboard click on Edit button.
            7. Add SpagoBI name on Menu field as per your requirement.
            8. Add SpagoBI sequence on Sequence field as per your requirement.
        4. SpagoBI page title change steps:-
            1. Open SpagoBI Web App folder "bista_spagobi_sso".
            2. Open bista_spagobi_sso -> view -> spagobi_app.xml on editor.
            3. Change field tag text as per your requirement.
            4. Change menu tag name as per your requirement.

    Specifications:-

    SpagoBI setup instructions:-

        1) Download & extract the All-In-One-SpagoBI-5.1.0_21012015.zip from
        spagobi website.
        2) Download and extract the package
        postgres-dbscript-4.0.0_11072013.zip from spagobi website.
        2) Change the default DB from HSQL to Postgres .(PostgreSQL as
        SpagoBI metadata repository)
        3) Create New Database
            • Create Database
            • Extract package postgres-dbscript-4.0.0_11072013.zip
            • Execute scripts into the newly created database:
            ◦ PG_create.sql
            ◦ PG_create_quartz_schema.sql
        4) Edit server.xml
            • Location: {All-In-One-SpagoBI-5.1.0_21012015 folder}/conf

            <Environment name="spagobi_resource_path"
            type="java.lang.String" value="${catalina.base}/resources"/>
            <Environment name="spagobi_sso_class" type="java.lang.String"
            value="it.eng.spagobi.services.common.FakeSsoService"/>
            <Environment name="spagobi_service_url" type="java.lang.String"
            value="http://{machine_ip}:{port}/SpagoBI"/>
            <Environment name="spagobi_host_url" type="java.lang.String"
            value="http://{machine_ip}:{port}"/>

            • Edit resource jdbc/spagobi
            <Resource name="jdbc/spagobi" auth="Container"
            type="javax.sql.DataSource" driverClassName="org.postgresql.Driver"
            url="jdbc:postgresql://{machine_ip}:{port}/{Database Name}"
            username="{user}" password="{password}" maxActive="20"
            maxIdle="10" maxWait="-1"/>
        5) Edit hibernate.cfg.xml
            • Location: {All-In-One-SpagoBI-5.1.0_21012015
            folder}/webapps/SpagoBI/WEB-INF/classes
            • Enable the hibernate dialect for PostgreSQL one and comment
            out the HSQLDialect
            (and other DBMS dialects if active) one
            <property name="hibernate.dialect">org.hibernate.dialect
            .PostgreSQLDialect</property>
            <!--<property name="hibernate.dialect">org.hibernate.dialect
            .HSQLDialect</property>-->
        6) Edit quartz.properties
            • Location: {All-In-One-SpagoBI-5.1.0_21012015
            folder}/webapps/SpagoBI/WEB-INF/classes
            • Enable the PostgreSQL dialect class and comment out the
            HSQLDialect (and other
            DBMS dialect classes if active) one
            #-------------- job store delegate class -------------------------
            # Hsqldb delegate class
            #org.quartz.jobStore.driverDelegate -
            #Class=org.quartz.impl.jdbcjobstore.HSQLDBDelegate
            # Mysql/Ingres delegate class
            #org.quartz.jobStore.driverDelegate -
            Class=org.quartz.impl.jdbcjobstore.StdJDBCDelegate
            Page 2 Of 17
            # Postgres delegate class
            org.quartz.jobStore.driverDelegate -
            Class=org.quartz.impl.jdbcjobstore.PostgreSQLDelegate
            # Oracle delegate class
            #org.quartz.jobStore.driverDelegate -
            Class=org.quartz.impl.jdbcjobstore.oracle.OracleDelegate
            # SQLServer delegate class
            #org.quartz.jobStore.driverDelegate -
            Class=org.quartz.impl.jdbcjobstore.MSSQLDelegate
            #-----------------------------------------------------------------
        7) Edit jbpm.hibernate.cfg.xml
            • Location: {All-In-One-SpagoBI-5.1.0_21012015
            folder}/webapps/SpagoBI/WEB-INF/classes
            • Enable the PostgreSQL dialect and comment out the HSQLDialect
            (and other DBMS
            dialects if active) one
            <hibernate-configuration>
            <session-factory>
            <!--property name="hibernate.dialect">
                org.hibernate.dialect.MySQLDialect
            </property-->
            <property name="hibernate.dialect">
                org.hibernate.dialect.PostgreSQLDialect
            </property>
            <!--property name="hibernate.dialect">
                org.hibernate.dialect.HSQLDialect
            </property-->
            <!-- jdbc connection properties -->
            <!-- property name="hibernate.dialect">
                org.hibernate.dialect.HSQLDialect
            </property-->
            <!-- property name="hibernate.dialect">
                org.hibernate.dialect.MySQLDialect
            </property-->
            <!-- property name="hibernate.dialect">
                org.hibernate.dialect.IngresDialect
            </property-->
            <!-- property name="hibernate.dialect">
                org.hibernate.dialect.SQLServerDialect
            </property-->
        8) Edit context.xml
            • Location: {All-In-One-SpagoBI-5.1.0_21012015 folder}/conf
            <Context useHttpOnly="false">
        9) Edit web.xml
            • Location: {All-In-One-SpagoBI-5.1.0_21012015\webapps\SpagoBI
            \WEB-INF
        <!-- OTHER CONFIGURATIONS -->
            <session-config>
                <session-timeout>30</session-timeout>
                <cookie-config>
                    <http-only>false</http-only>
                </cookie-config>
            </session-config>
        10) Edit weblogic.xml
            • Location: {All-In-One-SpagoBI-5.1.0_21012015\webapps\SpagoBI
            \WEB-INF
            <session-config>
              <cookie-config>
                <secure>false</secure>
                <http-only>false</http-only>
              </cookie-config>
            </session-config>
        11) Edit login.jsp and add above line in this jsp page
            • Location: All-In-One-SpagoBI-5.1.0_21012015\webapps\SpagoBI
            \themes\sbi_default\jsp
            var ca = document.cookie.split(';');
            console.log(ca);
            function createCookie(name,value,days) {
                if (days) {
                    var date = new Date();
                    date.setTime(date.getTime()+(days*24*60*60*1000));
                    var expires = "; expires="+date.toGMTString();
                }
                else var expires = "";
                document.cookie = name+"="+value+expires+"; path=/SpagoBI/";
            }
            function eraseCookie(name) {
                createCookie(name,"",-1);
            }
            eraseCookie("JSESSIONID");

        12) Replace the jar sbi.utils-5.1.0.jar to disable the password
        encryption
            • Location: All-In-One-SpagoBI-5.1.0_21012015\webapps\SpagoBI
            \WEB-INF\lib

        12) Restart the SpagoBI service using startup.bat
            Location: {All-In-One-SpagoBI-5.1.0_21012015 folder}/bin
            run startup.bat
""",
    'author': 'Rahul Malve',
    'depends': ['base'],
    'init_xml': [],
    'data': [
        'security/spagobi_security.xml',
        'security/ir.model.access.csv',
        'views/spagobi_app_views.xml',
        'views/spagobi_app_templates.xml',
        'views/res_users_view.xml',
        'views/spagobi_config_view.xml',
    ],
    'qweb': ['static/src/xml/spagobi_app.xml', ],
    'demo_xml': [],
    'test': [],
    'installable': True,
}
