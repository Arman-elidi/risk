"""
PDF Report Generation using WeasyPrint
Daily risk report with charts, tables, and executive summary
"""
from datetime import datetime, date
from typing import List, Dict
import io
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import plotly.graph_objects as go
import plotly.io as pio

from app.db.models import (
    Portfolio,
    RiskSnapshot,
    Alert,
    NewsEvent,
)

logger = structlog.get_logger()

# Configure Plotly for static image export
pio.kaleido.scope.mathjax = None


def generate_var_chart(snapshots: List[RiskSnapshot]) -> str:
    """Generate VaR time series chart as base64 PNG"""
    if not snapshots:
        return ""
    
    dates = [s.snapshot_date for s in snapshots]
    var_values = [s.var_1d_95 or 0 for s in snapshots]
    stressed_var_values = [s.stressed_var or 0 for s in snapshots]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=var_values,
        mode='lines+markers',
        name='VaR 1d 95%',
        line=dict(color='blue', width=2),
    ))
    fig.add_trace(go.Scatter(
        x=dates,
        y=stressed_var_values,
        mode='lines+markers',
        name='Stressed VaR',
        line=dict(color='red', width=2, dash='dash'),
    ))
    
    fig.update_layout(
        title='Value at Risk (30-day history)',
        xaxis_title='Date',
        yaxis_title='VaR (USD)',
        height=300,
        margin=dict(l=50, r=50, t=50, b=50),
    )
    
    # Convert to PNG base64
    img_bytes = fig.to_image(format='png', width=800, height=300)
    import base64
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    return f"data:image/png;base64,{img_base64}"


def generate_capital_chart(snapshot: RiskSnapshot) -> str:
    """Generate capital adequacy bar chart"""
    if not snapshot or not snapshot.total_k_req:
        return ""
    
    categories = ['K-NPR', 'K-AUM', 'K-CMH', 'K-COH']
    values = [
        snapshot.k_npr or 0,
        snapshot.k_aum or 0,
        snapshot.k_cmh or 0,
        snapshot.k_coh or 0,
    ]
    
    fig = go.Figure(data=[
        go.Bar(x=categories, y=values, marker_color='steelblue')
    ])
    
    fig.update_layout(
        title='Capital Requirements Breakdown',
        yaxis_title='Amount (USD)',
        height=300,
        margin=dict(l=50, r=50, t=50, b=50),
    )
    
    img_bytes = fig.to_image(format='png', width=600, height=300)
    import base64
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    return f"data:image/png;base64,{img_base64}"


def render_html_template(
    as_of_date: date,
    portfolios: List[Portfolio],
    snapshots: Dict[int, RiskSnapshot],
    alerts: List[Alert],
    news: List[NewsEvent],
    var_chart: str,
    capital_chart: str,
) -> str:
    """Render HTML template for PDF"""
    
    # Executive summary
    total_var = sum(s.var_1d_95 or 0 for s in snapshots.values())
    total_exposure = sum(s.total_exposure or 0 for s in snapshots.values())
    critical_alerts = [a for a in alerts if a.severity == 'CRITICAL']
    red_alerts = [a for a in alerts if a.severity == 'RED']
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Risk Report - {as_of_date}</title>
        <style>
            @page {{
                size: A4;
                margin: 2cm;
            }}
            body {{
                font-family: 'Arial', sans-serif;
                font-size: 11pt;
                line-height: 1.4;
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
            }}
            h2 {{
                color: #34495e;
                margin-top: 20px;
                border-bottom: 1px solid #bdc3c7;
                padding-bottom: 5px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
            }}
            th {{
                background-color: #3498db;
                color: white;
                padding: 8px;
                text-align: left;
            }}
            td {{
                padding: 6px 8px;
                border-bottom: 1px solid #ecf0f1;
            }}
            tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}
            .summary-box {{
                background-color: #ecf0f1;
                padding: 15px;
                margin: 15px 0;
                border-left: 4px solid #3498db;
            }}
            .alert-critical {{
                background-color: #e74c3c;
                color: white;
                padding: 10px;
                margin: 5px 0;
                border-radius: 3px;
            }}
            .alert-red {{
                background-color: #e67e22;
                color: white;
                padding: 10px;
                margin: 5px 0;
                border-radius: 3px;
            }}
            .alert-yellow {{
                background-color: #f39c12;
                color: white;
                padding: 8px;
                margin: 5px 0;
                border-radius: 3px;
            }}
            .metric {{
                display: inline-block;
                margin: 10px 15px 10px 0;
            }}
            .metric-label {{
                font-weight: bold;
                color: #7f8c8d;
            }}
            .metric-value {{
                font-size: 14pt;
                color: #2c3e50;
            }}
            .chart {{
                margin: 20px 0;
                text-align: center;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 10px;
                border-top: 1px solid #bdc3c7;
                font-size: 9pt;
                color: #7f8c8d;
            }}
        </style>
    </head>
    <body>
        <h1>Daily Risk Report</h1>
        <p><strong>Report Date:</strong> {as_of_date.strftime('%Y-%m-%d')}</p>
        <p><strong>Generated:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>
        
        <div class="summary-box">
            <h2>Executive Summary</h2>
            <div class="metric">
                <span class="metric-label">Total VaR (1d 95%):</span>
                <span class="metric-value">${total_var:,.0f}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Total Exposure:</span>
                <span class="metric-value">${total_exposure:,.0f}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Critical Alerts:</span>
                <span class="metric-value" style="color: #e74c3c;">{len(critical_alerts)}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Red Alerts:</span>
                <span class="metric-value" style="color: #e67e22;">{len(red_alerts)}</span>
            </div>
        </div>
        
        <h2>Portfolio Overview</h2>
        <table>
            <thead>
                <tr>
                    <th>Portfolio</th>
                    <th>DV01</th>
                    <th>VaR 1d 95%</th>
                    <th>Capital Ratio</th>
                    <th>LCR</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for portfolio in portfolios:
        snapshot = snapshots.get(portfolio.id)
        if snapshot:
            html += f"""
                <tr>
                    <td>{portfolio.name}</td>
                    <td>${snapshot.dv01_total or 0:,.0f}</td>
                    <td>${snapshot.var_1d_95 or 0:,.0f}</td>
                    <td>{snapshot.capital_ratio or 0:.2f}</td>
                    <td>{(snapshot.lcr_ratio or 0) * 100:.1f}%</td>
                </tr>
            """
    
    html += """
            </tbody>
        </table>
    """
    
    # VaR Chart
    if var_chart:
        html += f"""
        <h2>Value at Risk Trend</h2>
        <div class="chart">
            <img src="{var_chart}" style="max-width: 100%;" />
        </div>
        """
    
    # Capital Chart
    if capital_chart:
        html += f"""
        <h2>Capital Adequacy</h2>
        <div class="chart">
            <img src="{capital_chart}" style="max-width: 100%;" />
        </div>
        """
    
    # Alerts
    if critical_alerts or red_alerts:
        html += "<h2>Critical Alerts</h2>"
        
        for alert in critical_alerts:
            html += f"""
            <div class="alert-critical">
                <strong>{alert.metric_name or alert.alert_type}:</strong> {alert.description}
            </div>
            """
        
        for alert in red_alerts:
            html += f"""
            <div class="alert-red">
                <strong>{alert.metric_name or alert.alert_type}:</strong> {alert.description}
            </div>
            """
    
    # News
    if news:
        html += "<h2>Relevant News Events</h2>"
        html += "<ul>"
        for n in news[:5]:  # Top 5
            html += f"<li><strong>{n.event_date.strftime('%Y-%m-%d')}:</strong> {n.headline}</li>"
        html += "</ul>"
    
    html += """
        <div class="footer">
            <p>AI Risk Orchestrator v2.1 | Internal - Risk Management | Confidential</p>
            <p>This report is generated automatically. Please review alerts and take appropriate action.</p>
        </div>
    </body>
    </html>
    """
    
    return html


async def generate_daily_pdf(
    session: AsyncSession,
    as_of_date: date,
    output_path: str = None,
) -> str:
    """
    Generate daily PDF report
    
    Steps:
    1. Load all portfolios
    2. Load latest snapshots
    3. Load alerts
    4. Load news
    5. Generate charts
    6. Render HTML
    7. Convert to PDF
    8. Save to file or S3
    
    Returns:
        Path to generated PDF
    """
    logger.info("generate_daily_pdf_started", date=as_of_date)
    
    try:
        # 1. Load portfolios
        result = await session.execute(
            select(Portfolio).where(Portfolio.status == 'ACTIVE')
        )
        portfolios = list(result.scalars().all())
        
        # 2. Load snapshots for the date
        snapshots = {}
        for portfolio in portfolios:
            result = await session.execute(
                select(RiskSnapshot).where(
                    RiskSnapshot.portfolio_id == portfolio.id,
                    RiskSnapshot.snapshot_date == as_of_date,
                ).order_by(RiskSnapshot.calculation_timestamp.desc()).limit(1)
            )
            snapshot = result.scalar_one_or_none()
            if snapshot:
                snapshots[portfolio.id] = snapshot
        
        # 3. Load alerts for the date
        result = await session.execute(
            select(Alert).where(
                Alert.created_at >= as_of_date,
                Alert.severity.in_(['CRITICAL', 'RED', 'YELLOW']),
            ).order_by(Alert.severity, Alert.created_at.desc())
        )
        alerts = list(result.scalars().all())
        
        # 4. Load recent news
        result = await session.execute(
            select(NewsEvent).where(
                NewsEvent.event_date >= as_of_date,
            ).order_by(NewsEvent.importance.desc(), NewsEvent.event_date.desc()).limit(10)
        )
        news = list(result.scalars().all())
        
        # 5. Generate charts
        # VaR chart - need historical data
        if snapshots:
            first_snapshot = list(snapshots.values())[0]
            result = await session.execute(
                select(RiskSnapshot).where(
                    RiskSnapshot.portfolio_id == first_snapshot.portfolio_id,
                    RiskSnapshot.calculation_status == 'COMPLETED',
                ).order_by(RiskSnapshot.snapshot_date.desc()).limit(30)
            )
            historical = list(result.scalars().all())
            var_chart = generate_var_chart(historical)
            
            capital_chart = generate_capital_chart(first_snapshot)
        else:
            var_chart = ""
            capital_chart = ""
        
        # 6. Render HTML
        html_content = render_html_template(
            as_of_date,
            portfolios,
            snapshots,
            alerts,
            news,
            var_chart,
            capital_chart,
        )
        
        # 7. Convert to PDF
        font_config = FontConfiguration()
        pdf_bytes = HTML(string=html_content).write_pdf(font_config=font_config)
        
        # 8. Save to file
        if output_path is None:
            output_dir = Path("/tmp/risk_reports")
            output_dir.mkdir(exist_ok=True)
            output_path = str(output_dir / f"risk_report_{as_of_date}.pdf")
        
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)
        
        logger.info("generate_daily_pdf_completed", path=output_path, size_kb=len(pdf_bytes) / 1024)
        
        return output_path
        
    except Exception as e:
        logger.error("generate_daily_pdf_failed", error=str(e), exc_info=True)
        raise
