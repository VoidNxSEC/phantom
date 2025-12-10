#!/usr/bin/env python3
import os
import random
import json
import csv
import uuid
import time
import argparse
from datetime import datetime, timedelta

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# --- Data Generators ---

def generate_phone():
    return f"{random.randint(100,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}"

def generate_ssn():
    return f"{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(1000,9999)}"

def generate_cc():
    # Simple generator, not necessarily Luhn valid but matches regex
    return f"{random.randint(4000, 4999)} {random.randint(1000, 9999)} {random.randint(1000, 9999)} {random.randint(1000, 9999)}"

def generate_email(name):
    clean_name = name.lower().replace(' ', '.')
    domains = ['example.com', 'testcorp.org', 'fakedata.net', 'placeholder.io']
    return f"{clean_name}@{random.choice(domains)}"

def generate_name():
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
    last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"

# --- Content Generators ---

def create_employee_csv(filepath, count=50):
    with open(filepath, 'w', newline='') as csvfile:
        fieldnames = ['EmployeeID', 'Name', 'Email', 'Phone', 'SSN', 'Department', 'Role', 'Salary']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        depts = ['Engineering', 'HR', 'Sales', 'Marketing', 'Finance', 'Legal']
        roles = ['Manager', 'Associate', 'Director', 'Intern', 'VP']
        
        for i in range(count):
            name = generate_name()
            writer.writerow({
                'EmployeeID': f"EMP-{10000+i}",
                'Name': name,
                'Email': generate_email(name),
                'Phone': generate_phone(),
                'SSN': generate_ssn(),
                'Department': random.choice(depts),
                'Role': random.choice(roles),
                'Salary': random.randint(40000, 150000)
            })
    print(f"Generated {filepath} ({count} records)")

def create_credit_card_json(filepath, count=20):
    data = []
    for _ in range(count):
        name = generate_name()
        data.append({
            'card_id': str(uuid.uuid4()),
            'holder_name': name,
            'pan': generate_cc(),
            'cvv': f"{random.randint(100, 999)}",
            'expiry': f"{random.randint(1,12):02d}/{random.randint(24,30)}",
            'billing_address': f"{random.randint(100,9999)} Fake St, Springfield"
        })
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Generated {filepath} ({count} records)")

def create_chatbot_logs(filepath, count=10):
    conversations = []
    
    intents = [
        ("I need to reset my password", "Sure, I can help with that. What is your email?"),
        ("What is my account balance?", "Please provide your account ID."),
        ("I want to report a transaction", "Which transaction ID is it?"),
        ("Who is the CEO?", "Our CEO is John Doe.")
    ]
    
    sensitive_trigger = [
        ("Here is my API key: AKIAIOSFODNN7EXAMPLE", "Thank you, I have logged it."),
        ("My password is secret123!", "Please do not share passwords here."),
        ("I lost my card 4242-4242-4242-4242", "I will block it immediately.")
    ]

    for i in range(count):
        msgs = []
        base_time = datetime.now() - timedelta(days=random.randint(0, 30))
        
        # Start with a normal interaction
        user_q, bot_a = random.choice(intents)
        msgs.append({"role": "user", "timestamp": base_time.isoformat(), "message": user_q})
        msgs.append({"role": "bot", "timestamp": (base_time + timedelta(seconds=2)).isoformat(), "message": bot_a})
        
        # Maybe add something sensitive
        if random.random() < 0.3:
            sens_q, sens_a = random.choice(sensitive_trigger)
            msgs.append({"role": "user", "timestamp": (base_time + timedelta(seconds=10)).isoformat(), "message": sens_q})
            msgs.append({"role": "bot", "timestamp": (base_time + timedelta(seconds=12)).isoformat(), "message": sens_a})
            
        conversations.append({
            "session_id": str(uuid.uuid4()),
            "messages": msgs
        })

    with open(filepath, 'w') as f:
        # Saving as JSONL (line delimited JSON) or standard JSON
        if filepath.endswith('.jsonl'):
            for conv in conversations:
                f.write(json.dumps(conv) + '\n')
        else:
            json.dump(conversations, f, indent=2)
    print(f"Generated {filepath} ({count} conversations)")

def create_company_financials(filepath):
    # Generating a fake .xml or .csv report
    content = "Company,Year,Quarter,Revenue,Profit,Expenses,Notes\n"
    companies = ["Acme Corp", "Globex", "Soylent Corp", "Initech", "Umbrella Corp"]
    
    with open(filepath, 'w') as f:
        f.write(content)
        for comp in companies:
            for q in range(1, 5):
                rev = random.randint(1000000, 50000000)
                exp = int(rev * random.uniform(0.6, 0.9))
                prof = rev - exp
                note = ""
                if random.random() < 0.1:
                    note = "CONFIDENTIAL: Merger talks pending"
                f.write(f"{comp},2024,Q{q},{rev},{prof},{exp},{note}\n")
    print(f"Generated {filepath}")

def create_config_secrets(filepath):
    # Simulate a .env or config file
    secrets = [
        f"DB_PASSWORD=pass_{secrets_token()}",
        f"AWS_ACCESS_KEY_ID=AKIA{secrets_token().upper()[:16]}",
        f"AWS_SECRET_ACCESS_KEY={secrets_token()}{secrets_token()}",
        f"STRIPE_KEY=sk_live_{secrets_token()}",
        "DEBUG=true"
    ]
    with open(filepath, 'w') as f:
        f.write("\n".join(secrets))
    print(f"Generated {filepath}")

def secrets_token():
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=20))

# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="Generate placeholder data for testing.")
    parser.add_argument("-o", "--output", default="dummy_data", help="Output directory")
    args = parser.parse_args()

    ensure_dir(args.output)
    
    # Generate subdirectories to simulate structure
    ensure_dir(os.path.join(args.output, "hr"))
    ensure_dir(os.path.join(args.output, "finance"))
    ensure_dir(os.path.join(args.output, "logs"))
    ensure_dir(os.path.join(args.output, "configs"))

    # Generate files
    create_employee_csv(os.path.join(args.output, "hr", "employees_2024.csv"))
    create_employee_csv(os.path.join(args.output, "hr", "contractors.csv"), count=15)
    
    create_credit_card_json(os.path.join(args.output, "finance", "transactions_backup.json"))
    create_company_financials(os.path.join(args.output, "finance", "quarterly_report.csv"))
    
    create_chatbot_logs(os.path.join(args.output, "logs", "chat_history_oct.json"))
    create_chatbot_logs(os.path.join(args.output, "logs", "chat_history_nov.json"))
    
    create_config_secrets(os.path.join(args.output, "configs", ".env.production"))
    create_config_secrets(os.path.join(args.output, "configs", "server.conf"))

    print("\nData generation complete.")

if __name__ == "__main__":
    main()
