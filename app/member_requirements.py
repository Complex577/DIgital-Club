ALLOWED_COURSES = [
    "Bachelor of Computer Science",
    "Bachelor of Information Technology",
    "Bachelor of Software Engineering",
    "Bachelor of Data Science",
    "Bachelor of Cybersecurity",
    "Diploma in Computer Science",
    "Diploma in Information Technology",
    "Diploma in Software Engineering",
    "Diploma in Cybersecurity",
    "Certificate of Information Technology",
    "Non-Computing Program",
]

ALLOWED_YEARS = [
    "Year 1",
    "Year 2",
    "Year 3",
    "Year 4",
    "Graduate",
    "Alumni",
]


def is_allowed_course(course_value):
    return (course_value or "").strip() in ALLOWED_COURSES


def is_allowed_year(year_value):
    return (year_value or "").strip() in ALLOWED_YEARS
