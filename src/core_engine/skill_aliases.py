
# Must contain at least one of these "tech seed" tokens to be considered for ESCO phrase matching.
# Currently limited to certain domains (mostly software). You can expand this set if you want broader coverage, but be careful about false positives.
# For the current scope and time, I focused on software skills. 
# This project is scalable to other domains in the future if needed, but that would require more careful curation of both the seed tokens and the banned tokens.
TECH_SEED_TOKENS = {
    "python", "java", "django", "sql", "docker", "kubernetes", "terraform",
    "api", "apis", "linux", "cloud", "aws", "azure", "security", "networking",
    "storage", "ci", "cd", "cicd", "prometheus", "grafana", "opentelemetry",
    "inference", "serving", "distributed",
}

# -----------------------------
# High-precision alias layer
# -----------------------------
# Map many ways of writing a skill -> canonical display label
SKILL_ALIASES: dict[str, str] = {

    # -------------------------
    # Programming languages
    # -------------------------
    "python": "Python",
    "java": "Java",
    "c#": "C#",
    "c sharp": "C#",
    "c++": "C++",
    "cpp": "C++",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "go": "Go",
    "golang": "Go",
    "rust": "Rust",
    "kotlin": "Kotlin",
    "swift": "Swift",
    "scala": "Scala",
    "r": "R",
    "ruby": "Ruby",
    "php": "PHP",
    "bash": "Bash",
    "shell scripting": "Shell scripting",
    "powershell": "PowerShell",
    "matlab": "MATLAB",
    "julia": "Julia",
    "solidity": "Solidity",

    # -------------------------
    # Web / backend frameworks
    # -------------------------
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "spring": "Spring",
    "spring boot": "Spring Boot",
    "express": "Express.js",
    "express.js": "Express.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "rails": "Ruby on Rails",
    "ruby on rails": "Ruby on Rails",
    "laravel": "Laravel",
    "asp.net": "ASP.NET",
    "dotnet": ".NET",
    ".net": ".NET",

    # -------------------------
    # Frontend frameworks / tools
    # -------------------------
    "react": "React",
    "vue": "Vue.js",
    "vue.js": "Vue.js",
    "angular": "Angular",
    "svelte": "Svelte",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "html": "HTML",
    "css": "CSS",
    "sass": "Sass",
    "tailwind": "Tailwind CSS",
    "tailwind css": "Tailwind CSS",
    "webpack": "Webpack",
    "vite": "Vite",
    "jest": "Jest",
    "cypress": "Cypress",
    "selenium": "Selenium",
    "bootstrap": "Bootstrap",

    # -------------------------
    # APIs and protocols
    # -------------------------
    "rest api": "REST API",
    "rest apis": "REST API",
    "restful api": "REST API",
    "restful apis": "REST API",
    "graphql": "GraphQL",
    "grpc": "gRPC",
    "websockets": "WebSockets",
    "oauth": "OAuth",
    "oauth2": "OAuth2",
    "jwt": "JWT",
    "openapi": "OpenAPI",
    "swagger": "Swagger",

    # -------------------------
    # Databases - relational
    # -------------------------
    "sql": "SQL",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mysql": "MySQL",
    "sqlite": "SQLite",
    "oracle": "Oracle DB",
    "oracle db": "Oracle DB",
    "ms sql": "Microsoft SQL Server",
    "sql server": "Microsoft SQL Server",
    "microsoft sql server": "Microsoft SQL Server",
    "t-sql": "T-SQL",
    "plsql": "PL/SQL",
    "pl/sql": "PL/SQL",
    "relational database": "Relational databases",
    "relational databases": "Relational databases",

    # -------------------------
    # Databases - NoSQL / other
    # -------------------------
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "redis": "Redis",
    "cassandra": "Cassandra",
    "dynamodb": "DynamoDB",
    "elasticsearch": "Elasticsearch",
    "neo4j": "Neo4j",
    "firebase": "Firebase",
    "couchdb": "CouchDB",
    "nosql": "NoSQL",

    # -------------------------
    # Data warehousing / analytics DBs
    # -------------------------
    "snowflake": "Snowflake",
    "bigquery": "BigQuery",
    "redshift": "Amazon Redshift",
    "amazon redshift": "Amazon Redshift",
    "synapse": "Azure Synapse",
    "azure synapse": "Azure Synapse",
    "databricks": "Databricks",
    "dbt": "dbt",
    "data warehouse": "Data warehousing",
    "data warehousing": "Data warehousing",
    "dimensional modelling": "Dimensional modelling",
    "dimensional modeling": "Dimensional modelling",
    "star schema": "Star schema",
    "data modelling": "Data modelling",
    "data modeling": "Data modelling",

    # -------------------------
    # Data engineering / pipelines
    # -------------------------
    "etl": "ETL",
    "elt": "ELT",
    "airflow": "Apache Airflow",
    "apache airflow": "Apache Airflow",
    "spark": "Apache Spark",
    "apache spark": "Apache Spark",
    "kafka": "Apache Kafka",
    "apache kafka": "Apache Kafka",
    "flink": "Apache Flink",
    "apache flink": "Apache Flink",
    "hadoop": "Hadoop",
    "hive": "Apache Hive",
    "apache hive": "Apache Hive",
    "dask": "Dask",
    "data pipeline": "Data pipelines",
    "data pipelines": "Data pipelines",

    # -------------------------
    # Data science / ML libraries
    # -------------------------
    "pandas": "pandas",
    "numpy": "NumPy",
    "scipy": "SciPy",
    "matplotlib": "Matplotlib",
    "seaborn": "Seaborn",
    "plotly": "Plotly",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "xgboost": "XGBoost",
    "lightgbm": "LightGBM",
    "tensorflow": "TensorFlow",
    "keras": "Keras",
    "pytorch": "PyTorch",
    "torch": "PyTorch",
    "hugging face": "Hugging Face",
    "transformers": "Transformers",
    "langchain": "LangChain",
    "openai api": "OpenAI API",
    "machine learning": "Machine learning",
    "deep learning": "Deep learning",
    "natural language processing": "NLP",
    "nlp": "NLP",
    "computer vision": "Computer vision",
    "reinforcement learning": "Reinforcement learning",
    "feature engineering": "Feature engineering",
    "model training": "Model training",
    "model evaluation": "Model evaluation",
    "model deployment": "Model deployment",
    "mlops": "MLOps",
    "mlflow": "MLflow",
    "weights and biases": "Weights & Biases",

    # -------------------------
    # Cloud platforms
    # -------------------------
    "aws": "AWS",
    "amazon web services": "AWS",
    "azure": "Microsoft Azure",
    "microsoft azure": "Microsoft Azure",
    "gcp": "Google Cloud",
    "google cloud": "Google Cloud",
    "google cloud platform": "Google Cloud",
    "ec2": "AWS EC2",
    "s3": "AWS S3",
    "lambda": "AWS Lambda",
    "cloudwatch": "AWS CloudWatch",
    "rds": "AWS RDS",
    "eks": "AWS EKS",
    "aks": "Azure AKS",
    "gke": "Google GKE",

    # -------------------------
    # DevOps / infrastructure
    # -------------------------
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "helm": "Helm",
    "terraform": "Terraform",
    "ansible": "Ansible",
    "puppet": "Puppet",
    "chef": "Chef",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "github actions": "GitHub Actions",
    "jenkins": "Jenkins",
    "gitlab ci": "GitLab CI",
    "circleci": "CircleCI",
    "argocd": "ArgoCD",
    "flux": "Flux",
    "gitops": "GitOps",
    "infrastructure as code": "Infrastructure as Code",
    "iac": "Infrastructure as Code",
    "service mesh": "Service mesh",
    "istio": "Istio",

    # -------------------------
    # Observability / monitoring
    # -------------------------
    "prometheus": "Prometheus",
    "grafana": "Grafana",
    "opentelemetry": "OpenTelemetry",
    "datadog": "Datadog",
    "new relic": "New Relic",
    "splunk": "Splunk",
    "elk stack": "ELK Stack",
    "elasticsearch kibana": "ELK Stack",
    "observability": "Observability",
    "incident response": "Incident response",
    "on-call": "On-call",

    # -------------------------
    # Version control / collaboration
    # -------------------------
    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",
    "bitbucket": "Bitbucket",
    "jira": "Jira",
    "confluence": "Confluence",
    "agile": "Agile",
    "scrum": "Scrum",
    "kanban": "Kanban",
    "sprint planning": "Sprint planning",

    # -------------------------
    # Testing
    # -------------------------
    "unit testing": "Unit testing",
    "integration testing": "Integration testing",
    "integration tests": "Integration testing",
    "end-to-end testing": "End-to-end testing",
    "e2e testing": "End-to-end testing",
    "test-driven development": "TDD",
    "tdd": "TDD",
    "pytest": "pytest",
    "junit": "JUnit",
    "postman": "Postman",
    "performance testing": "Performance testing",
    "load testing": "Load testing",
    "penetration testing": "Penetration testing",
    "pen testing": "Penetration testing",
    "testing": "Testing",

    # -------------------------
    # Systems / networking / security
    # -------------------------
    "linux": "Linux",
    "unix": "Unix",
    "windows server": "Windows Server",
    "networking": "Networking",
    "tcp/ip": "TCP/IP",
    "dns": "DNS",
    "http": "HTTP",
    "https": "HTTPS",
    "ssl": "SSL/TLS",
    "tls": "SSL/TLS",
    "vpn": "VPN",
    "firewall": "Firewall",
    "distributed systems": "Distributed systems",
    "microservices": "Microservices",
    "load balancing": "Load balancing",
    "caching": "Caching",
    "message queue": "Message queuing",
    "message queuing": "Message queuing",
    "security": "Security",
    "cybersecurity": "Cybersecurity",
    "cyber security": "Cybersecurity",
    "owasp": "OWASP",
    "siem": "SIEM",
    "soc": "SOC",
    "vulnerability assessment": "Vulnerability assessment",
    "cryptography": "Cryptography",
    "sandboxing": "Sandboxing",
    "workload isolation": "Workload isolation",
    "identity management": "Identity management",
    "iam": "IAM",
    "zero trust": "Zero Trust",
    "gdpr": "GDPR",
    "iso 27001": "ISO 27001",

    # -------------------------
    # AI infrastructure
    # -------------------------
    "model serving": "Model serving",
    "inference": "Inference",
    "model inference": "Inference",
    "open source": "Open source",
    "open-source": "Open source",
    "storage": "Storage",
    "performance": "Performance",
    "scalability": "Scalability",

    # -------------------------
    # Mobile development
    # -------------------------
    "ios": "iOS development",
    "android": "Android development",
    "react native": "React Native",
    "flutter": "Flutter",
    "swiftui": "SwiftUI",
    "jetpack compose": "Jetpack Compose",
    "xcode": "Xcode",
    "android studio": "Android Studio",

    # -------------------------
    # Data governance / architecture
    # -------------------------
    "data governance": "Data governance",
    "data quality": "Data quality",
    "data lineage": "Data lineage",
    "data catalogue": "Data catalogue",
    "data catalog": "Data catalogue",
    "metadata management": "Metadata management",
    "data mesh": "Data mesh",
    "data lake": "Data lake",
    "data lakehouse": "Data lakehouse",
    "data architecture": "Data architecture",
    "enterprise architecture": "Enterprise architecture",
    "solution architecture": "Solution architecture",
    "cloud architecture": "Cloud architecture",
    "database design": "Database design",
    "schema design": "Schema design",
    "erp": "ERP systems",
    "erp systems": "ERP systems",
    "sap": "SAP",
    "salesforce": "Salesforce",
    "power bi": "Power BI",
    "tableau": "Tableau",
    "looker": "Looker",
    "excel": "Microsoft Excel",
    "microsoft excel": "Microsoft Excel",

    # -------------------------
    # Finance / accounting
    # -------------------------
    "financial modelling": "Financial modelling",
    "financial modeling": "Financial modelling",
    "financial analysis": "Financial analysis",
    "budgeting": "Budgeting",
    "forecasting": "Forecasting",
    "valuation": "Valuation",
    "dcf": "DCF analysis",
    "dcf analysis": "DCF analysis",
    "ifrs": "IFRS",
    "uk gaap": "UK GAAP",
    "gaap": "GAAP",
    "audit": "Audit",
    "risk management": "Risk management",
    "compliance": "Compliance",
    "accounting": "Accounting",
    "bookkeeping": "Bookkeeping",
    "tax": "Taxation",
    "taxation": "Taxation",
    "bloomberg": "Bloomberg Terminal",
    "bloomberg terminal": "Bloomberg Terminal",
    "quantitative analysis": "Quantitative analysis",
    "statistical analysis": "Statistical analysis",
    "time series": "Time series analysis",
    "time series analysis": "Time series analysis",

    # -------------------------
    # Marketing / digital
    # -------------------------
    "seo": "SEO",
    "sem": "SEM",
    "google analytics": "Google Analytics",
    "google ads": "Google Ads",
    "facebook ads": "Facebook Ads",
    "meta ads": "Meta Ads",
    "email marketing": "Email marketing",
    "content marketing": "Content marketing",
    "social media marketing": "Social media marketing",
    "copywriting": "Copywriting",
    "hubspot": "HubSpot",
    "mailchimp": "Mailchimp",
    "a/b testing": "A/B testing",
    "conversion rate optimisation": "CRO",
    "cro": "CRO",
    "crm": "CRM",
    "customer segmentation": "Customer segmentation",
    "market research": "Market research",

    # -------------------------
    # HR / people
    # -------------------------
    "recruitment": "Recruitment",
    "talent acquisition": "Talent acquisition",
    "onboarding": "Onboarding",
    "performance management": "Performance management",
    "employee relations": "Employee relations",
    "hris": "HRIS",
    "workday": "Workday",
    "bamboohr": "BambooHR",
    "employment law": "Employment law",
    "payroll": "Payroll",

    # -------------------------
    # Project / product management
    # -------------------------
    "project management": "Project management",
    "product management": "Product management",
    "stakeholder management": "Stakeholder management",
    "requirements gathering": "Requirements gathering",
    "user stories": "User stories",
    "product roadmap": "Product roadmap",
    "okrs": "OKRs",
    "kpis": "KPIs",
    "prince2": "PRINCE2",
    "pmp": "PMP",

    # -------------------------
    # Design / UX
    # -------------------------
    "ux design": "UX design",
    "ui design": "UI design",
    "ux research": "UX research",
    "user research": "User research",
    "figma": "Figma",
    "sketch": "Sketch",
    "adobe xd": "Adobe XD",
    "wireframing": "Wireframing",
    "prototyping": "Prototyping",
    "usability testing": "Usability testing",
    "accessibility": "Accessibility",
    "wcag": "WCAG",

    # -------------------------
    # Legal / compliance
    # -------------------------
    "contract drafting": "Contract drafting",
    "legal research": "Legal research",
    "due diligence": "Due diligence",
    "mergers and acquisitions": "M&A",
    "m&a": "M&A",
    "litigation": "Litigation",
    "data protection": "Data protection",
    "intellectual property": "Intellectual property",
    "ip law": "Intellectual property",

    # -------------------------
    # Engineering (non-software)
    # -------------------------
    "autocad": "AutoCAD",
    "revit": "Revit",
    "civil 3d": "Civil 3D",
    "solidworks": "SolidWorks",
    "finite element analysis": "FEA",
    "fea": "FEA",
    "cad": "CAD",
    "bim": "BIM",
    "structural analysis": "Structural analysis",
    "hydraulic modelling": "Hydraulic modelling",
    "hydraulic modeling": "Hydraulic modelling",
    "gis": "GIS",
    "qgis": "QGIS",
    "arcgis": "ArcGIS",

    # -------------------------
    # Soft / transferable
    # -------------------------
    "stakeholder communication": "Stakeholder communication",
    "technical writing": "Technical writing",
    "documentation": "Documentation",
    "public speaking": "Public speaking",
    "data-driven decision making": "Data-driven decision making",
    "problem solving": "Problem solving",
    "critical thinking": "Critical thinking",
    "team leadership": "Team leadership",
    "mentoring": "Mentoring",
    "code review": "Code review",
    "pair programming": "Pair programming",
}

