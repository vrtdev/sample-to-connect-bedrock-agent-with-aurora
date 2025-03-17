import boto3
import json

# Define your AWS Aurora PostgreSQL configuration
CLUSTER_ARN = "Update with RDSAuroraStack.CLUSTERARN"  # Replace with your cluster ARN
ADMIN_SECRET_ARN = "Update with RDSAuroraStack.ADMINSECRETARN"  # Replace with your secret ARN
DB_NAME = "postgres"  # Replace with your database name

# Initialize RDS Data client
rds_data = boto3.client("rds-data")


def execute_statement(sql, parameters=[]):
    response = rds_data.execute_statement(
        resourceArn=CLUSTER_ARN,
        secretArn=ADMIN_SECRET_ARN,
        database=DB_NAME,
        sql=sql,
        parameters=parameters,
    )
    return response


def create_schema_and_ingest_data():

    # Cleanup existing schemas

    drops = [
        "DROP SCHEMA academics CASCADE;",
        "DROP SCHEMA staff CASCADE;",
        "DROP SCHEMA facilities CASCADE;",
        "DROP SCHEMA research CASCADE;",
    ]

    # Schema creation statements
    schemas = [
        "CREATE SCHEMA IF NOT EXISTS academics;",
        "CREATE SCHEMA IF NOT EXISTS staff;",
        "CREATE SCHEMA IF NOT EXISTS facilities;",
        "CREATE SCHEMA IF NOT EXISTS research;",
    ]

    # Table creation statements
    tables = [
        """
        CREATE TABLE IF NOT EXISTS academics.departments (
            department_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            code VARCHAR(10) UNIQUE NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS academics.courses (
            course_id SERIAL PRIMARY KEY,
            department_id INTEGER REFERENCES academics.departments(department_id),
            code VARCHAR(20) UNIQUE NOT NULL,
            title VARCHAR(200) NOT NULL,
            credits INTEGER NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS academics.students (
            student_id SERIAL PRIMARY KEY,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            date_of_birth DATE NOT NULL,
            enrollment_date DATE NOT NULL,
            major_department_id INTEGER REFERENCES academics.departments(department_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS academics.enrollments (
            enrollment_id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES academics.students(student_id),
            course_id INTEGER REFERENCES academics.courses(course_id),
            semester VARCHAR(20) NOT NULL,
            year INTEGER NOT NULL,
            grade CHAR(2)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS staff.employees (
            employee_id SERIAL PRIMARY KEY,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            hire_date DATE NOT NULL,
            position VARCHAR(100) NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS facilities.buildings (
            building_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            address VARCHAR(200) NOT NULL,
            construction_year INTEGER
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS research.projects (
            project_id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            start_date DATE,
            end_date DATE,
            funding_amount DECIMAL(12, 2)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS research.publications (
            publication_id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            authors TEXT NOT NULL,
            publication_date DATE,
            journal VARCHAR(200),
            doi VARCHAR(100)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS research.project_members (
            project_id INTEGER REFERENCES research.projects(project_id),
            employee_id INTEGER REFERENCES staff.employees(employee_id),
            role VARCHAR(50) NOT NULL,
            PRIMARY KEY (project_id, employee_id)
        );
        """,
    ]

    # Execute drop statements
    print("Cleaning up existing schemas...")
    for drop in drops:
        execute_statement(drop)

    # Execute schema creation
    print("Creating schemas...")
    for schema in schemas:
        execute_statement(schema)

    # Execute table creation
    print("Creating tables...")
    for table in tables:
        execute_statement(table)

    schemas = [
        "academics",
        "staff",
        "facilities",
        "research",
    ]
    # grant read-only permissions to all schemas
    # User and readonly_role are created already in the RDSAuroraStack
    grants = []
    for schema in schemas:
        grants.append(f"GRANT USAGE ON SCHEMA {schema} TO readonly_role")
        grants.append(f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema} TO readonly_role")
        grants.append(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT SELECT ON TABLES TO readonly_role"
        )

    # Execute each statement using Data API
    print("Adding grant...")
    for grant in grants:
        execute_statement(grant)

    # Sample data insertion
    print("Inserting sample data...")
    sample_data = [
        (
            "INSERT INTO academics.departments (name, code) VALUES (:name, :code)",
            [
                [
                    {"name": "name", "value": {"stringValue": "Computer Science"}},
                    {"name": "code", "value": {"stringValue": "CS"}},
                ],
                [
                    {"name": "name", "value": {"stringValue": "Physics"}},
                    {"name": "code", "value": {"stringValue": "PHY"}},
                ],
                [
                    {"name": "name", "value": {"stringValue": "Mathematics"}},
                    {"name": "code", "value": {"stringValue": "MATH"}},
                ],
            ],
        ),
        (
            "INSERT INTO academics.courses (department_id, code, title, credits) VALUES (:dept_id, :code, :title, :credits)",
            [
                [
                    {"name": "dept_id", "value": {"longValue": 1}},
                    {"name": "code", "value": {"stringValue": "CS101"}},
                    {
                        "name": "title",
                        "value": {"stringValue": "Introduction to Programming"},
                    },
                    {"name": "credits", "value": {"longValue": 3}},
                ],
                [
                    {"name": "dept_id", "value": {"longValue": 2}},
                    {"name": "code", "value": {"stringValue": "PHY201"}},
                    {"name": "title", "value": {"stringValue": "Classical Mechanics"}},
                    {"name": "credits", "value": {"longValue": 4}},
                ],
                [
                    {"name": "dept_id", "value": {"longValue": 3}},
                    {"name": "code", "value": {"stringValue": "MATH301"}},
                    {"name": "title", "value": {"stringValue": "Linear Algebra"}},
                    {"name": "credits", "value": {"longValue": 3}},
                ],
            ],
        ),
        (
            "INSERT INTO academics.students (first_name, last_name, date_of_birth, enrollment_date, major_department_id) VALUES (:fname, :lname, CAST(:dob AS DATE), CAST(:enroll_date AS DATE), :dept_id)",
            [
                [
                    {"name": "fname", "value": {"stringValue": "John"}},
                    {"name": "lname", "value": {"stringValue": "Doe"}},
                    {"name": "dob", "value": {"stringValue": "2000-01-15"}},
                    {"name": "enroll_date", "value": {"stringValue": "2022-09-01"}},
                    {"name": "dept_id", "value": {"longValue": 1}},
                ],
                [
                    {"name": "fname", "value": {"stringValue": "Jane"}},
                    {"name": "lname", "value": {"stringValue": "Smith"}},
                    {"name": "dob", "value": {"stringValue": "2001-03-22"}},
                    {"name": "enroll_date", "value": {"stringValue": "2022-09-01"}},
                    {"name": "dept_id", "value": {"longValue": 2}},
                ],
                [
                    {"name": "fname", "value": {"stringValue": "Alice"}},
                    {"name": "lname", "value": {"stringValue": "Johnson"}},
                    {"name": "dob", "value": {"stringValue": "2000-07-30"}},
                    {"name": "enroll_date", "value": {"stringValue": "2022-09-01"}},
                    {"name": "dept_id", "value": {"longValue": 3}},
                ],
            ],
        ),
        (
            "INSERT INTO academics.enrollments (student_id, course_id, semester, year, grade) VALUES (:student_id, :course_id, :semester, :year, :grade)",
            [
                [
                    {"name": "student_id", "value": {"longValue": 1}},  # Alice Johnson
                    {"name": "course_id", "value": {"longValue": 1}},  # CS101
                    {"name": "semester", "value": {"stringValue": "Fall"}},
                    {"name": "year", "value": {"longValue": 2022}},
                    {"name": "grade", "value": {"stringValue": "A"}},
                ],
                [
                    {"name": "student_id", "value": {"longValue": 1}},  # Alice Johnson
                    {"name": "course_id", "value": {"longValue": 2}},  # PHY201
                    {"name": "semester", "value": {"stringValue": "Spring"}},
                    {"name": "year", "value": {"longValue": 2023}},
                    {"name": "grade", "value": {"stringValue": "B+"}},
                ],
                [
                    {"name": "student_id", "value": {"longValue": 2}},  # Bob Smith
                    {"name": "course_id", "value": {"longValue": 2}},  # PHY201
                    {"name": "semester", "value": {"stringValue": "Fall"}},
                    {"name": "year", "value": {"longValue": 2022}},
                    {"name": "grade", "value": {"stringValue": "A-"}},
                ],
                [
                    {"name": "student_id", "value": {"longValue": 2}},  # Bob Smith
                    {"name": "course_id", "value": {"longValue": 3}},  # BIO301
                    {"name": "semester", "value": {"stringValue": "Spring"}},
                    {"name": "year", "value": {"longValue": 2023}},
                    {"name": "grade", "value": {"stringValue": "B"}},
                ],
                [
                    {"name": "student_id", "value": {"longValue": 1}},  # Alice Johnson
                    {"name": "course_id", "value": {"longValue": 3}},  # BIO301
                    {"name": "semester", "value": {"stringValue": "Spring"}},
                    {"name": "year", "value": {"longValue": 2023}},
                    {"name": "grade", "value": {"stringValue": "A"}},
                ],
                [
                    {"name": "student_id", "value": {"longValue": 2}},  # Bob Smith
                    {"name": "course_id", "value": {"longValue": 1}},  # CS101
                    {"name": "semester", "value": {"stringValue": "Fall"}},
                    {"name": "year", "value": {"longValue": 2023}},
                    {
                        "name": "grade",
                        "value": {"stringValue": ""},
                    },  # Currently enrolled, no grade yet
                ],
            ],
        ),
        (
            "INSERT INTO staff.employees (first_name, last_name, email, hire_date, position) VALUES (:fname, :lname, :email, CAST(:hire_date AS DATE), :position)",
            [
                [
                    {"name": "fname", "value": {"stringValue": "Robert"}},
                    {"name": "lname", "value": {"stringValue": "Brown"}},
                    {
                        "name": "email",
                        "value": {"stringValue": "robert.brown@university.edu"},
                    },
                    {"name": "hire_date", "value": {"stringValue": "2015-08-15"}},
                    {"name": "position", "value": {"stringValue": "Professor"}},
                ],
                [
                    {"name": "fname", "value": {"stringValue": "Emily"}},
                    {"name": "lname", "value": {"stringValue": "Davis"}},
                    {
                        "name": "email",
                        "value": {"stringValue": "emily.davis@university.edu"},
                    },
                    {"name": "hire_date", "value": {"stringValue": "2018-01-10"}},
                    {
                        "name": "position",
                        "value": {"stringValue": "Associate Professor"},
                    },
                ],
                [
                    {"name": "fname", "value": {"stringValue": "Michael"}},
                    {"name": "lname", "value": {"stringValue": "Wilson"}},
                    {
                        "name": "email",
                        "value": {"stringValue": "michael.wilson@university.edu"},
                    },
                    {"name": "hire_date", "value": {"stringValue": "2020-07-01"}},
                    {
                        "name": "position",
                        "value": {"stringValue": "Assistant Professor"},
                    },
                ],
            ],
        ),
        (
            "INSERT INTO facilities.buildings (name, address, construction_year) VALUES (:name, :address, :year)",
            [
                [
                    {"name": "name", "value": {"stringValue": "Science Building"}},
                    {"name": "address", "value": {"stringValue": "123 University Ave"}},
                    {"name": "year", "value": {"longValue": 1985}},
                ],
                [
                    {"name": "name", "value": {"stringValue": "Library"}},
                    {"name": "address", "value": {"stringValue": "456 College St"}},
                    {"name": "year", "value": {"longValue": 1990}},
                ],
                [
                    {"name": "name", "value": {"stringValue": "Student Center"}},
                    {"name": "address", "value": {"stringValue": "789 Campus Rd"}},
                    {"name": "year", "value": {"longValue": 2005}},
                ],
            ],
        ),
        (
            "INSERT INTO research.projects (title, description, start_date, end_date, funding_amount) VALUES (:title, :desc, CAST(:start AS DATE), CAST(:end AS DATE), :amount)",
            [
                [
                    {"name": "title", "value": {"stringValue": "AI in Education"}},
                    {
                        "name": "desc",
                        "value": {
                            "stringValue": "Exploring AI applications in higher education"
                        },
                    },
                    {"name": "start", "value": {"stringValue": "2023-01-01"}},
                    {"name": "end", "value": {"stringValue": "2025-12-31"}},
                    {"name": "amount", "value": {"doubleValue": 500000.00}},
                ],
                [
                    {
                        "name": "title",
                        "value": {"stringValue": "Quantum Computing Advances"},
                    },
                    {
                        "name": "desc",
                        "value": {"stringValue": "Research on quantum algorithms"},
                    },
                    {"name": "start", "value": {"stringValue": "2022-07-01"}},
                    {"name": "end", "value": {"stringValue": "2024-06-30"}},
                    {"name": "amount", "value": {"doubleValue": 750000.00}},
                ],
                [
                    {
                        "name": "title",
                        "value": {"stringValue": "Climate Change Mitigation"},
                    },
                    {
                        "name": "desc",
                        "value": {
                            "stringValue": "Studying effective climate change mitigation strategies"
                        },
                    },
                    {"name": "start", "value": {"stringValue": "2023-03-15"}},
                    {"name": "end", "value": {"stringValue": "2026-03-14"}},
                    {"name": "amount", "value": {"doubleValue": 1000000.00}},
                ],
            ],
        ),
        # Add this to the sample_data list in create_schema_and_ingest_data() function
        (
            "INSERT INTO research.publications (title, authors, publication_date, journal, doi) VALUES (:title, :authors, CAST(:pub_date AS DATE), :journal, :doi)",
            [
                [
                    {
                        "name": "title",
                        "value": {
                            "stringValue": "Advances in Quantum Computing Algorithms"
                        },
                    },
                    {
                        "name": "authors",
                        "value": {
                            "stringValue": "Robert Brown, Emily Davis, Michael Wilson"
                        },
                    },
                    {
                        "name": "pub_date",
                        "value": {"stringValue": "2023-06-15"},
                    },
                    {
                        "name": "journal",
                        "value": {"stringValue": "Journal of Quantum Computing"},
                    },
                    {
                        "name": "doi",
                        "value": {"stringValue": "10.1234/jqc.2023.001"},
                    },
                ],
                [
                    {
                        "name": "title",
                        "value": {
                            "stringValue": "Machine Learning in Climate Prediction"
                        },
                    },
                    {
                        "name": "authors",
                        "value": {"stringValue": "Emily Davis, Alice Johnson"},
                    },
                    {
                        "name": "pub_date",
                        "value": {"stringValue": "2023-08-20"},
                    },
                    {
                        "name": "journal",
                        "value": {"stringValue": "Environmental Science & Technology"},
                    },
                    {
                        "name": "doi",
                        "value": {"stringValue": "10.1234/est.2023.045"},
                    },
                ],
                [
                    {
                        "name": "title",
                        "value": {
                            "stringValue": "Neural Networks in Educational Assessment"
                        },
                    },
                    {
                        "name": "authors",
                        "value": {"stringValue": "Michael Wilson, Robert Brown"},
                    },
                    {
                        "name": "pub_date",
                        "value": {"stringValue": "2023-09-30"},
                    },
                    {
                        "name": "journal",
                        "value": {"stringValue": "Educational Technology Research"},
                    },
                    {
                        "name": "doi",
                        "value": {"stringValue": "10.1234/etr.2023.078"},
                    },
                ],
            ],
        ),
        (
            "INSERT INTO research.project_members (project_id, employee_id, role) VALUES (:project_id, :employee_id, :role)",
            [
                [
                    {
                        "name": "project_id",
                        "value": {"longValue": 1},  # AI in Education project
                    },
                    {"name": "employee_id", "value": {"longValue": 1}},  # Robert Brown
                    {
                        "name": "role",
                        "value": {"stringValue": "Principal Investigator"},
                    },
                ],
                [
                    {
                        "name": "project_id",
                        "value": {"longValue": 1},  # AI in Education project
                    },
                    {
                        "name": "employee_id",
                        "value": {"longValue": 3},  # Michael Wilson
                    },
                    {"name": "role", "value": {"stringValue": "Co-Investigator"}},
                ],
                [
                    {
                        "name": "project_id",
                        "value": {"longValue": 2},  # Quantum Computing Advances project
                    },
                    {"name": "employee_id", "value": {"longValue": 2}},  # Emily Davis
                    {
                        "name": "role",
                        "value": {"stringValue": "Principal Investigator"},
                    },
                ],
                [
                    {
                        "name": "project_id",
                        "value": {"longValue": 2},  # Quantum Computing Advances project
                    },
                    {"name": "employee_id", "value": {"longValue": 1}},  # Robert Brown
                    {"name": "role", "value": {"stringValue": "Research Associate"}},
                ],
                [
                    {
                        "name": "project_id",
                        "value": {"longValue": 3},  # Climate Change Mitigation project
                    },
                    {
                        "name": "employee_id",
                        "value": {"longValue": 3},  # Michael Wilson
                    },
                    {
                        "name": "role",
                        "value": {"stringValue": "Principal Investigator"},
                    },
                ],
                [
                    {
                        "name": "project_id",
                        "value": {"longValue": 3},  # Climate Change Mitigation project
                    },
                    {"name": "employee_id", "value": {"longValue": 2}},  # Emily Davis
                    {"name": "role", "value": {"stringValue": "Research Scientist"}},
                ],
            ],
        ),
    ]

    # Execute data insertion
    for sql, data in sample_data:
        for item in data:
            execute_statement(sql, item)


def main():
    # Validate configuration
    if not all([CLUSTER_ARN, ADMIN_SECRET_ARN, DB_NAME]):
        print(
            "Error: Please configure CLUSTER_ARN, ADMIN_SECRET_ARN, and DB_NAME in the script"
        )
        return 1

    try:
        print("Starting database schema creation and data ingestion...")
        create_schema_and_ingest_data()
        print("Successfully created schema and ingested sample data!")
        return 0
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())
