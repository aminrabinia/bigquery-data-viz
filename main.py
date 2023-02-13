
import uvicorn
import gradio as gr
import numpy as np
import plotly.express as px
from google.cloud import bigquery
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.glissai.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get('/')
def root():
    return {"message": "hello from data viz!"}

client = bigquery.Client.from_service_account_json("jsonkey.json")

QUERY_base = (" FROM `data-science-proj-376319.nypd_motor_vehicle_collisions.nypd_mv_collisions` " 
    " WHERE timestamp between '2021-01-01' and '2022-01-01' ")

def run_query():
    QUERY = "SELECT on_street_name as street, contributing_factor_vehicle_1 as cause, unique_key, vehicle_type_code1 as vehicle, timestamp " \
        + QUERY_base + " LIMIT 10 "

    query_job = client.query(QUERY)  
    query_result = query_job.result()  
    df = query_result.to_dataframe()

    df = df[["unique_key", "vehicle", "cause", "street", "timestamp"]] # Select a subset of columns 
    df = df.astype({"unique_key": np.int64}) # Convert numeric columns to standard numpy types
    return df

def run_query2():
    QUERY = "SELECT count(unique_key) as collisions, contributing_factor_vehicle_1 as cause, extract(month FROM timestamp) as month " \
        + QUERY_base + " GROUP BY month, cause ORDER BY month"

    query_job = client.query(QUERY)  
    query_result = query_job.result()  
    df = query_result.to_dataframe()
    
    df = df[["collisions", "month", "cause"]] # Select a subset of columns 
    df = df.astype({"collisions": np.int64, "month": np.int64}) # Convert numeric columns to standard numpy types
    return df


async def show_chart(causes):

    df = run_query2()
    # Filter the data by "cause"
    df = df[df.cause.isin(causes)]

    fig = px.line(df, x="month", y='collisions', color='cause')
    fig.update_layout(
    title="Colisions ",
    xaxis_title="Month",
    yaxis_title="Number of Collisions")
    return fig


inputs = [gr.CheckboxGroup(
                ["Alcohol Involvement", "Backing Unsafely", "Driver Inattention/Distraction", "Fell Asleep", 
                 "Following Too Closely", "Steering Failure", "Traffic Control Disregarded", "Unsafe Speed"], 
                label="Cause", 
                value=["Alcohol Involvement", "Backing Unsafely"]),]
outputs = gr.Plot()

with gr.Blocks(css="footer {visibility: hidden}") as chart_demo:
    gr.Markdown("# NYPD Collisions Dataset")
    with gr.Row():
        gr.Interface(
            fn=show_chart,
            inputs=inputs,
            outputs=outputs,
            allow_flagging='never', 
            live = False)

with gr.Blocks(css="footer {visibility: hidden}") as table_demo:
    gr.Markdown("# NYPD Collisions Dataset")
    with gr.Row():
        gr.DataFrame(run_query, max_rows=10, overflow_row_behaviour='paginate')

demo = gr.TabbedInterface([chart_demo, table_demo],["Chart", "Table"], css="footer {visibility: hidden}")

gr.mount_gradio_app(app, demo, path="/gradio")


if __name__ == "__main__":

     uvicorn.run(app, host='0.0.0.0', port=8080)