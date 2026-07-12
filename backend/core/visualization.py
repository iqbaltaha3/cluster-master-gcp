"""
core/visualization.py
Reusable Plotly chart builders.
"""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np


def scatter_2d(coords, labels, title="Cluster Visualization (2D)", hover_data=None):
    df = pd.DataFrame({"x": coords[:, 0], "y": coords[:, 1], "cluster": labels.astype(str)})
    if hover_data is not None:
        for k, v in hover_data.items():
            df[k] = v
    fig = px.scatter(
        df, x="x", y="y", color="cluster", title=title,
        hover_data=list(hover_data.keys()) if hover_data else None,
        opacity=0.8,
    )
    fig.update_layout(legend_title_text="Cluster")
    return fig


def scatter_3d(coords, labels, title="Cluster Visualization (3D)"):
    df = pd.DataFrame({"x": coords[:, 0], "y": coords[:, 1], "z": coords[:, 2], "cluster": labels.astype(str)})
    fig = px.scatter_3d(df, x="x", y="y", z="z", color="cluster", title=title, opacity=0.8)
    return fig


def correlation_heatmap(df: pd.DataFrame, numeric_cols):
    corr = df[numeric_cols].corr()
    fig = px.imshow(
        corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
        title="Correlation Heatmap"
    )
    return fig


def histogram(df: pd.DataFrame, col):
    fig = px.histogram(df, x=col, marginal="box", title=f"Distribution of {col}")
    return fig


def boxplot(df: pd.DataFrame, col, by=None):
    fig = px.box(df, y=col, x=by, title=f"Boxplot of {col}" + (f" by {by}" if by else ""))
    return fig


def elbow_plot(ks, inertias):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ks, y=inertias, mode="lines+markers"))
    fig.update_layout(title="Elbow Method (KMeans Inertia)", xaxis_title="Number of Clusters (k)", yaxis_title="Inertia")
    return fig


def radar_chart(categories, values_by_cluster, title="Cluster Profile Comparison"):
    fig = go.Figure()
    for cluster_name, values in values_by_cluster.items():
        fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill="toself", name=str(cluster_name)))
    fig.update_layout(title=title, polar=dict(radialaxis=dict(visible=True)))
    return fig


def bar_chart(x, y, title, xlabel="", ylabel=""):
    fig = go.Figure(go.Bar(x=x, y=y))
    fig.update_layout(title=title, xaxis_title=xlabel, yaxis_title=ylabel)
    return fig


def cluster_size_pie(labels):
    vals, counts = np.unique(labels, return_counts=True)
    fig = px.pie(names=[f"Cluster {v}" if v != -1 else "Noise" for v in vals], values=counts, title="Cluster Size Distribution")
    return fig
