# Career Fair Queue Manager

    pip install -r requirements.txt
    python generate_sample_csv.py        # only if you don't have career_fair_1000.csv
    uvicorn main:app --reload
    python -m pytest

The CSV must contain `Student_ID` and `Est_Interaction_Time_Mins`; other columns are kept as JSON in `students.extra`.
Override locations with `CAREER_FAIR_CSV` and `CAREER_FAIR_DB`. Docs at `/docs`.
