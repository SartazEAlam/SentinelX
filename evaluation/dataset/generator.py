"""Synthetic dataset generator for SentinelX Phase 9 evaluation.

Generates realistic synthetic data samples covering:
- Sensitive categories (Credentials, Payment Cards, Identity, Contact, API Keys, Employee, Confidential Docs, Source Code)
- Non-sensitive / Benign categories (Public docs, Generic business notes, Benign code, Public numbers)
- Realistic Edge Cases (Benign text with sensitive keywords, card-like tracking numbers, public support emails)

Strictly uses SYNTHETIC mock strings. NEVER includes real secrets or private data.
"""

import json
from pathlib import Path
import random

RANDOM_SEED = 42

def build_synthetic_samples() -> list[dict]:
    """Constructs a deterministic collection of 600 synthetic evaluation samples."""
    random.seed(RANDOM_SEED)
    
    samples = []
    sample_id = 1
    
    # =========================================================================
    # 1. SENSITIVE SAMPLES (Total: 300)
    # =========================================================================
    
    # 1.1 CREDENTIALS (40 samples)
    credential_templates = [
        "DB_PASSWORD=demo_secret_pass_{i}!",
        "admin_password = 'SecretAdminKey{i}#$'",
        "redis://user:p@ssword{i}_secret@cache.internal.net:6379",
        "DATABASE_URL=postgres://app_user:db_pass_xyz_{i}@db.prod.internal/main",
        "mongodb+srv://admin:ClusterPass{i}99@cluster0.internal.net/analytics",
        "export FTP_PASSWORD='SuperSafeFtpPass{i}!'",
        "vault_token: s.mockVaultTokenForDevTesting{i}",
        "root:x:0:0:root:/root:/bin/bash\nservice_account:$6$dummy_salt_{i}$hash_placeholder",
        "Here are your initial credentials: username: jdoe, temporary_password: InitPass{i}!@#",
        "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC3MockRsaKeyLine{i} root@internal-host",
    ]
    for i in range(4):
        for tmpl in credential_templates:
            samples.append({
                "id": f"SENS_CRED_{sample_id:04d}",
                "text": tmpl.format(i=sample_id),
                "is_sensitive": True,
                "category": "CREDENTIALS",
                "filename": f"config_{sample_id}.env" if i % 2 == 0 else f"database_{sample_id}.conf",
            })
            sample_id += 1

    # 1.2 PAYMENT_CARD_DATA (40 samples)
    card_templates = [
        "Customer payment processed: Card number 411122223333{last4:04d}, exp 12/28, CVV 842",
        "Billing account update: Visa ending in 453201509988{last4:04d}, cardholder: Alex Morgan",
        "MasterCard auth token requested for 510510510510{last4:04d}, expiration date 09/27",
        "Amex corporate transaction: 37828224631{last4:04d}, amount $1,420.50",
        "Please charge 400012345678{last4:04d} for invoice #99281, authorization approved",
        "Direct debit card recorded: 555555555555{last4:04d}, auth code: 49201",
        "Merchant terminal swipe record: Pan: 424242424242{last4:04d} Service code: 201",
        "Card entry: 34000000000{last4:04d} Exp: 04/29 Zip: 90210",
        "Batch card reconciliation: 520082828282{last4:04d} status approved",
        "Credit card storage record: 412345678901{last4:04d} holder: Jordan Lee",
    ]
    for i in range(4):
        for tmpl in card_templates:
            samples.append({
                "id": f"SENS_CARD_{sample_id:04d}",
                "text": tmpl.format(last4=(sample_id % 9000) + 1000),
                "is_sensitive": True,
                "category": "PAYMENT_CARD_DATA",
                "filename": f"transactions_{sample_id}.csv" if i % 2 == 0 else f"billing_export_{sample_id}.txt",
            })
            sample_id += 1

    # 1.3 IDENTITY_INFORMATION (35 samples)
    identity_templates = [
        "Employee SSN record: 987-{i:02d}-4321, Full Name: Taylor Swiftly",
        "Applicant background verification: Social Security: 123-{i:02d}-6789, DOB: 1985-04-12",
        "Tax filing form W-2: Taxpayer SSN: 456-{i:02d}-0123, Adjusted Gross Income: $84,200",
        "HR compliance record: SSN 000-{i:02d}-9999 for identity verification step 2",
        "Government ID verification: US Passport #P{i:06d}84, Country of Issuance: USA",
        "Identity docket: SSN 999-{i:02d}-1111, Driver License: DL{i:08d}TX",
        "Patient identity registry: SSN: 321-{i:02d}-9876, State ID: CA{i:07d}",
    ]
    for i in range(5):
        for tmpl in identity_templates:
            samples.append({
                "id": f"SENS_ID_{sample_id:04d}",
                "text": tmpl.format(i=sample_id % 90 + 10),
                "is_sensitive": True,
                "category": "IDENTITY_INFORMATION",
                "filename": f"hr_compliance_{sample_id}.xlsx" if i % 2 == 0 else f"identity_verification_{sample_id}.txt",
            })
            sample_id += 1

    # 1.4 API_KEYS & TOKENS (45 samples)
    api_key_templates = [
        "aws_secret_access_key = 'mock_aws_secret_access_key_{i:02d}_simulated'",
        "AWS_ACCESS_KEY_ID = 'mock_aws_access_key_id_{i:02d}_simulated'",
        "GITHUB_TOKEN = 'mock_github_personal_token_{i:04d}_simulated'",
        "api_key = 'mock_stripe_secret_token_{i:04d}xyz_simulated'",
        "SLACK_BOT_TOKEN = 'mock_slack_bot_token_{i:04d}_simulated'",
        "SENDGRID_API_KEY = 'mock_sendgrid_secret_key_{i:04d}_simulated'",
        "const OPENAI_API_KEY = 'mock_openai_secret_token_{i:04d}_simulated';",
        "authorization_token = 'mock_bearer_jwt_authorization_token_{i:04d}'",
        "api_secret = 'mock_api_secret_key_token_{i:04d}_simulated'",
    ]
    for i in range(5):
        for tmpl in api_key_templates:
            samples.append({
                "id": f"SENS_API_{sample_id:04d}",
                "text": tmpl.format(i=sample_id),
                "is_sensitive": True,
                "category": "API_KEYS",
                "filename": f"secrets_{sample_id}.py" if i % 2 == 0 else f"deploy_keys_{sample_id}.env",
            })
            sample_id += 1

    # 1.5 EMPLOYEE_DATA / SALARY (40 samples)
    employee_templates = [
        "Executive payroll memo: John Doe, Chief Architect, base salary $245,000, bonus 25%",
        "Confidential compensation review: Staff salary band 7 approved at $175,000 per annum",
        "HR Payroll run: Employee ID EMP{i:05d}, Net Pay: $6,420.00, Direct deposit account verified",
        "Annual bonus allocation table: Engineering Lead bonus compensation $35,000 payable Q1",
        "Employee compensation ledger: department=Security, base_salary=$190000, equity_grant=4500",
        "Staff payroll list: ID={i:04d}, Role=Senior Developer, Monthly Salary=$12,500",
        "Internal salary adjustment request for contractor team, hourly rate increased to $145/hr",
        "Termination severance package: Employee #EMP{i:05d}, severance payout $48,000",
    ]
    for i in range(5):
        for tmpl in employee_templates:
            samples.append({
                "id": f"SENS_EMP_{sample_id:04d}",
                "text": tmpl.format(i=sample_id),
                "is_sensitive": True,
                "category": "EMPLOYEE_DATA",
                "filename": f"salary_report_{sample_id}.csv" if i % 2 == 0 else f"payroll_q3_{sample_id}.txt",
            })
            sample_id += 1

    # 1.6 CONFIDENTIAL_DOCUMENT (50 samples)
    confidential_templates = [
        "CONFIDENTIAL AND PROPRIETARY: Strategic acquisition roadmap for Project Titan Q4",
        "STRICTLY CONFIDENTIAL: Merger & acquisition preliminary term sheet between Sentinel Corp and Target Ltd",
        "INTERNAL USE ONLY: Board of Directors meeting minutes regarding Q3 financial performance and layoffs",
        "Proprietary architectural blueprint: Next-generation quantum-resistant encryption engine v2",
        "Restricted distribution: Customer vulnerability assessment report detailing unpatched CVEs in core api",
        "Attorney-client privileged communication regarding pending intellectual property patent dispute",
        "Confidential product roadmap: Unannounced zero-trust enterprise agent launch scheduled for November",
        "Trade secret disclosure: Proprietary heuristic scoring formula and machine learning weights",
        "Confidential audit findings: Major compliance deficiency observed in EU customer data segregation",
        "Privileged risk assessment memo: Impact analysis of internal source code repository exfiltration",
    ]
    for i in range(5):
        for tmpl in confidential_templates:
            samples.append({
                "id": f"SENS_CONF_{sample_id:04d}",
                "text": tmpl,
                "is_sensitive": True,
                "category": "CONFIDENTIAL_DOCUMENT",
                "filename": f"confidential_memo_{sample_id}.docx" if i % 2 == 0 else f"internal_strategy_{sample_id}.pdf",
            })
            sample_id += 1

    # 1.7 CONTACT_INFORMATION & SENSITIVE EMAILS (50 samples)
    contact_templates = [
        "Confidential customer contact: Director Sarah Connor, direct email: sarah.connor{i}@vip-client.corp, phone: +1-555-019-2831",
        "VIP customer escalation registry: contact email mark.watney{i}@aero-defense.gov, secure cell: (555) 948-2019",
        "Executive emergency contact roster: CTO email david.banner{i}@gamma-labs.org, mobile: +44 20 7946 09{i:02d}",
        "Whistleblower confidential tip contact: anon_source{i}@protonmail-secure.ch, phone: +1-202-555-0143",
        "Private client database: Name: Elizabeth Bennet, Email: ebennet{i}@estate-trust.co.uk, Telephone: 07700 900{i:03d}",
    ]
    for i in range(10):
        for tmpl in contact_templates:
            samples.append({
                "id": f"SENS_CONT_{sample_id:04d}",
                "text": tmpl.format(i=sample_id),
                "is_sensitive": True,
                "category": "CONTACT_INFORMATION",
                "filename": f"customer_contacts_{sample_id}.csv" if i % 2 == 0 else f"vip_roster_{sample_id}.txt",
            })
            sample_id += 1


    # =========================================================================
    # 2. NON-SENSITIVE / BENIGN SAMPLES (Total: 300)
    # =========================================================================

    # 2.1 PUBLIC DOCUMENTATION & MARKETING (60 samples)
    public_templates = [
        "SentinelX is an intelligent Data Loss Prevention system designed to detect and prevent unauthorized exfiltration.",
        "Apache License 2.0: You may reproduce and distribute copies of the Work in any medium, with or without modifications.",
        "Press Release: Open Source Community releases new version 4.2 of the data visualization library.",
        "Getting Started Guide: To install the package, execute `npm install --save my-package` in your terminal.",
        "System requirements: Minimum 4GB RAM, dual-core CPU, and 20GB of available disk space required.",
        "Our customer support team is available 24/7 to answer general inquiries about service uptime and features.",
        "Release Notes v1.2: Fixed minor rendering bug on high-DPI displays and optimized image caching mechanism.",
        "The annual cybersecurity symposium will be held in San Francisco from October 12 to 14, 2026.",
        "Read our whitepaper on Modern Zero Trust Network Architecture and Endpoint Security Best Practices.",
        "API Reference Guide: The `/health` endpoint returns HTTP 200 OK with the current service status.",
    ]
    for i in range(6):
        for tmpl in public_templates:
            samples.append({
                "id": f"BEN_PUB_{sample_id:04d}",
                "text": tmpl,
                "is_sensitive": False,
                "category": "PUBLIC_DOCUMENTATION",
                "filename": f"readme_{sample_id}.md" if i % 2 == 0 else f"documentation_{sample_id}.html",
            })
            sample_id += 1

    # 2.2 GENERIC BUSINESS / OFFICE MESSAGES (60 samples)
    office_templates = [
        "Reminder: The kitchen refrigerator will be cleaned on Friday afternoon at 4:00 PM. Please label your food.",
        "Thanks for the update on the sprint board. Let us review the user stories during the morning standup.",
        "Office supply order placed: whiteboard markers, printer paper, sticky notes, and replacement coffee filters.",
        "The conference room projector is now working properly after the cable replacement.",
        "Team lunch vote: Please react with pizza or sushi emoji to choose tomorrow's catered lunch.",
        "Good morning team, please make sure your timecards are submitted by end of day today.",
        "Happy work anniversary to our front-end engineer on completing 3 years with the company!",
        "The AC maintenance in building B is scheduled for Saturday morning between 9 AM and 1 PM.",
        "Please remember to mute your microphone when not speaking during large group meetings.",
        "The company book club will discuss chapters 4 and 5 of Designing Data-Intensive Applications on Thursday.",
    ]
    for i in range(6):
        for tmpl in office_templates:
            samples.append({
                "id": f"BEN_OFF_{sample_id:04d}",
                "text": tmpl,
                "is_sensitive": False,
                "category": "GENERIC_TEXT",
                "filename": f"announcement_{sample_id}.txt" if i % 2 == 0 else f"slack_archive_{sample_id}.txt",
            })
            sample_id += 1

    # 2.3 BENIGN SOURCE CODE (60 samples)
    code_templates = [
        "def calculate_fibonacci(n):\n    if n <= 1: return n\n    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)",
        "import React from 'react';\nexport const Button = ({ label, onClick }) => <button onClick={onClick}>{label}</button>;",
        "const calculateDiscount = (price, rate) => {\n  const discount = price * (rate / 100);\n  return price - discount;\n};",
        ".header-container {\n  display: flex;\n  justify-content: space-between;\n  align-items: center;\n  padding: 1rem;\n}",
        "SELECT department_id, COUNT(*) AS employee_count FROM departments GROUP BY department_id ORDER BY employee_count DESC;",
        "class TemperatureConverter:\n    @staticmethod\n    def celsius_to_fahrenheit(c):\n        return (c * 9/5) + 32",
        "// Unit test for string manipulation utility\ndescribe('slugify', () => {\n  it('converts title to kebab-case', () => {\n    expect(slugify('Hello World')).toBe('hello-world');\n  });\n});",
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head><title>Home Page</title></head>\n<body><h1>Welcome to our Portal</h1></body>\n</html>",
        "import math\ndef compute_hypotenuse(a: float, b: float) -> float:\n    return math.sqrt(a**2 + b**2)",
        "git checkout -b feature/new-login-ui\ngit add .\ngit commit -m 'Implement responsive layout'",
    ]
    for i in range(6):
        for tmpl in code_templates:
            samples.append({
                "id": f"BEN_CODE_{sample_id:04d}",
                "text": tmpl,
                "is_sensitive": False,
                "category": "BENIGN_CODE",
                "filename": f"utility_{sample_id}.py" if i % 2 == 0 else f"component_{sample_id}.tsx",
            })
            sample_id += 1

    # 2.4 NORMAL NUMERICAL & LOG DATA (60 samples)
    numeric_templates = [
        "Server uptime report: System active for 142 days, 18 hours, 32 minutes without restart.",
        "Public company earnings: Total revenue for Q2 reached $42.5 million, up 12% year-over-year.",
        "Warehouse inventory count: SKU-998821 quantity: 420 units, warehouse location: Aisle 4, Shelf 12.",
        "Flight schedule: Flight AA-1049 departing JFK at 08:30 EST, arriving LAX at 11:45 PST.",
        "Telemetry metric: CPU load 18.4%, memory utilization 42.1%, disk I/O 2.3 MB/s.",
        "HTTP 200 GET /index.html 192.168.1.1 Mozilla/5.0 45ms bytes_sent=14092",
        "Event counter: Total website visitors today: 184,920 unique IP addresses recorded.",
        "Weather station telemetry: Temperature 22.4 C, Humidity 58%, Barometric Pressure 1013.2 hPa.",
        "Order shipment tracking status: Package #99281-TRACK delivery confirmed at front porch.",
        "Benchmark run #42 completed in 1.482 seconds across 10,000 simulated iterations.",
    ]
    for i in range(6):
        for tmpl in numeric_templates:
            samples.append({
                "id": f"BEN_NUM_{sample_id:04d}",
                "text": tmpl,
                "is_sensitive": False,
                "category": "NORMAL_NUMBERS",
                "filename": f"metrics_{sample_id}.log" if i % 2 == 0 else f"inventory_{sample_id}.csv",
            })
            sample_id += 1

    # 2.5 REALISTIC CHALLENGING EDGE CASES (60 samples)
    edge_templates = [
        # Mentions "password" in educational / security policy context
        "Always choose a strong, unique password consisting of letters, numbers, and symbols for each account.",
        "Password managers allow users to store complex credentials securely without writing them down on sticky notes.",
        "To reset your forgotten password, click the public recovery link on our help center webpage.",
        # Mentions "salary" in industry research context
        "According to the 2025 Tech Careers Survey, average software engineering salaries grew by 4.2% nationwide.",
        "Negotiating your base salary requires understanding industry benchmarks and market rate data points.",
        # Mentions "credit card" in general informational context
        "Credit card processing fees typically range between 1.5% and 3.5% per merchant transaction.",
        "Learn the difference between debit card and credit card consumer fraud protection rights under Federal law.",
        # Number sequences that look like cards or SSNs but are tracking or order numbers
        "Shipping tracking code: 4111-9988-2233 (UPS ground delivery parcel identifier).",
        "Invoice order number: INV-123-45-6789 created for office stationery bulk purchase.",
        "Public support contact for general questions: info@example-company.org, toll-free 1-800-555-0199.",
        "Customer feedback ticket #49281: 'The checkout page button was easy to click, great job!'",
        "Our public GitHub repository contains open source documentation and example code templates.",
    ]
    for i in range(5):
        for tmpl in edge_templates:
            samples.append({
                "id": f"BEN_EDGE_{sample_id:04d}",
                "text": tmpl,
                "is_sensitive": False,
                "category": "EDGE_CASE_BENIGN",
                "filename": f"blog_post_{sample_id}.md" if i % 2 == 0 else f"security_tips_{sample_id}.txt",
            })
            sample_id += 1

    # Shuffle deterministically
    random.shuffle(samples)
    return samples

def main():
    dataset_dir = Path(__file__).resolve().parent
    dataset_file = dataset_dir / "synthetic_data.json"
    stats_file = dataset_dir / "dataset_stats.json"

    samples = build_synthetic_samples()

    # Calculate statistics
    total = len(samples)
    sensitive_count = sum(1 for s in samples if s["is_sensitive"])
    benign_count = total - sensitive_count
    
    categories = {}
    for s in samples:
        cat = s["category"]
        categories[cat] = categories.get(cat, 0) + 1

    stats = {
        "total_samples": total,
        "sensitive_samples": sensitive_count,
        "sensitive_percentage": round(sensitive_count / total * 100, 2),
        "benign_samples": benign_count,
        "benign_percentage": round(benign_count / total * 100, 2),
        "random_seed": RANDOM_SEED,
        "category_distribution": categories,
    }

    with open(dataset_file, "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2)

    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    print(f"Generated {total} synthetic evaluation samples.")
    print(f"Sensitive: {sensitive_count} ({stats['sensitive_percentage']}%)")
    print(f"Benign: {benign_count} ({stats['benign_percentage']}%)")
    print(f"Saved to {dataset_file} and {stats_file}")

if __name__ == "__main__":
    main()
