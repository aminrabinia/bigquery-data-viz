import uvicorn
import numpy as np
import gradio as gr
from google.cloud import bigquery
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


client = bigquery.Client.from_service_account_json("jsonkey.json")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.glissai.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get('/')
def root():
    return {"message": "hello!"}



QUERY = (
    "SELECT on_street_name as street, contributing_factor_vehicle_1 as cause, unique_key, vehicle_type_code1 as vehicle, timestamp "
    "FROM `data-science-proj-376319.nypd_motor_vehicle_collisions.nypd_mv_collisions` " 
    "where timestamp between '2021-01-01' and '2022-01-01'  "
    "LIMIT 10")

def run_query():
    query_job = client.query(QUERY)  
    # print('job: ', query_job)
    query_result = query_job.result()  
    # print('results: ', query_result)
    df = query_result.to_dataframe()
    # print('df: ', df)
    # Select a subset of columns 
    df = df[["unique_key", "vehicle", "cause", "street", "timestamp"]]
    # Convert numeric columns to standard numpy types
    df = df.astype({"unique_key": np.int64})
    return df

QUERY2 = (
    "SELECT count(unique_key) as collisions, extract(month FROM timestamp) as month "
    "FROM `data-science-proj-376319.nypd_motor_vehicle_collisions.nypd_mv_collisions` " 
    "where timestamp between '2021-01-01' and '2022-01-01' group by month order by month")

def run_query2():
    query_job = client.query(QUERY2)  
    query_result = query_job.result()  
    df = query_result.to_dataframe()
    # Select a subset of columns 
    df = df[["collisions", "month"]]
    # Convert numeric columns to standard numpy types
    df = df.astype({"collisions": np.int64, "month": np.int64})
    return df



with gr.Blocks(css="footer {visibility: hidden}") as demo:
    gr.Markdown("# NYPD Collisions Dataset")
    with gr.Row():
        gr.DataFrame(run_query, max_rows=10, overflow_row_behaviour='paginate')
        gr.LinePlot(run_query2, x="month", y="collisions", width=500, height=500)

gr.mount_gradio_app(app, demo, path="/gradio")


if __name__ == "__main__":

     uvicorn.run(app, host='0.0.0.0', port=8080)