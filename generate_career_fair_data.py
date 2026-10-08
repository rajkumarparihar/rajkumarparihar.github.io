"""Generate a simulated dataset of 1,000 career fair attendees.

Usage:
    pip install faker pandas
    python generate_career_fair_data.py
"""

import random

import pandas as pd
from faker import Faker

NUM_ATTENDEES = 1000
SEED = 42
OUTPUT_FILE = "career_fair_1000.csv"

MAJOR_WEIGHTS = {
    "Computer Science": 30,
    "Data Science": 22,
    "Analytics": 18,
    "Information Systems": 7,
    "Software Engineering": 6,
    "Cybersecurity": 4,
    "Electrical Engineering": 3,
    "Mechanical Engineering": 3,
    "Mathematics": 2,
    "Statistics": 2,
    "Business Administration": 2,
    "Marketing": 1,
}

ROLES_BY_MAJOR = {
    "Computer Science": [
        "Software Engineer Intern",
        "Backend Developer",
        "Cloud Engineer",
        "Machine Learning Engineer",
        "Full-Stack Developer",
    ],
    "Data Science": [
        "Data Scientist Intern",
        "Machine Learning Engineer",
        "Data Engineer",
        "AI Research Intern",
        "Data Analyst",
    ],
    "Analytics": [
        "Business Analyst",
        "Data Analyst",
        "Analytics Consultant",
        "BI Developer",
        "Data Scientist Intern",
    ],
    "Information Systems": [
        "IT Analyst",
        "Systems Analyst",
        "Product Analyst",
        "Cloud Engineer",
    ],
    "Software Engineering": [
        "Software Engineer Intern",
        "DevOps Engineer",
        "Backend Developer",
        "QA Automation Engineer",
    ],
    "Cybersecurity": [
        "Security Analyst",
        "Cloud Security Engineer",
        "Penetration Tester",
    ],
    "Electrical Engineering": [
        "Embedded Systems Engineer",
        "Hardware Engineer",
        "Automotive Software Engineer",
    ],
    "Mechanical Engineering": [
        "Automotive Engineer",
        "Manufacturing Engineer",
        "Product Design Engineer",
    ],
    "Mathematics": ["Quantitative Analyst", "Data Scientist Intern", "Data Analyst"],
    "Statistics": ["Statistician", "Data Analyst", "Data Scientist Intern"],
    "Business Administration": [
        "Product Manager Intern",
        "Business Analyst",
        "Technical Program Manager",
    ],
    "Marketing": ["Digital Marketing Analyst", "Product Marketing Intern"],
}

COMPANY_WEIGHTS = {
    "Cox Automotive": 20,
    "Adobe": 17,
    "Mercedes-Benz": 15,
    "Google Cloud": 20,
    "Microsoft": 5,
    "Amazon Web Services": 5,
    "Delta Air Lines": 4,
    "NCR Voyix": 3,
    "Georgia-Pacific": 3,
    "Home Depot": 3,
    "Salesforce": 3,
    "Deloitte": 2,
}


def weighted_choice(rng, weights):
    return rng.choices(list(weights), weights=list(weights.values()), k=1)[0]


def generate_attendees(n=NUM_ATTENDEES, seed=SEED):
    rng = random.Random(seed)
    fake = Faker("en_US")
    Faker.seed(seed)

    student_ids = rng.sample(range(10_000_000, 99_999_999), n)

    rows = []
    for sid in student_ids:
        major = weighted_choice(rng, MAJOR_WEIGHTS)
        rows.append(
            {
                "Student_ID": f"S{sid}",
                "Name": fake.name(),
                "Major": major,
                "Desired_Role": rng.choice(ROLES_BY_MAJOR[major]),
                "Target_Company": weighted_choice(rng, COMPANY_WEIGHTS),
                "Est_Interaction_Time_Mins": rng.randint(1, 5),
            }
        )
    return pd.DataFrame(rows)


def main():
    df = generate_attendees()
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved {len(df)} attendees to {OUTPUT_FILE}")
    print(df.head(), end="\n\n")
    print("Major distribution (%):")
    print((df["Major"].value_counts(normalize=True) * 100).round(1), end="\n\n")
    print("Target company distribution (%):")
    print((df["Target_Company"].value_counts(normalize=True) * 100).round(1))


if __name__ == "__main__":
    main()
