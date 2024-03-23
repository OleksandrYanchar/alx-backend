from datetime import date
from pathlib import Path

import aiofiles

async def calculate_percentage_change(old_value, new_value):
    new_value = int(new_value)
    old_value = int(old_value)
    
    if new_value == 0 and old_value == 0:
        return "0.0"  # If both values are zero, the percentage change is 0%
    elif new_value == 0:
        return "-100.0"  # If the new value is zero, it's a 100% decrease
    elif old_value == 0:
        return "Infinity"  # If the old value is zero, it's an infinite increase percentage-wise
    elif old_value > new_value:
        percentage_change = new_value / old_value *-100
    else:
        percentage_change = new_value / old_value *100
    return f"{round(percentage_change, 2)}"






async def generate_report_file(report_data: dict):
    root = Path(__file__).parent.parent
    template_path = root / "templates" / "report.html"
    
    async with aiofiles.open(template_path, mode='r') as file:
        template_content = await file.read()

    # Using string's format method to substitute placeholders with actual values
    filled_html = template_content.format(
        report_date=date.today().isoformat(),
        total_users=report_data.get('total_users', 'N/A'),
        total_activated=report_data.get('total_activated', 'N/A'),
        new_users=report_data.get('new_users', 'N/A'),
        total_vips=report_data.get('total_vips', 'N/A'),
        new_vips=report_data.get('new_vips', 'N/A'),
        total_posts=report_data.get('total_posts', 'N/A'),
        new_posts=report_data.get('new_posts', 'N/A'),
        posts_average_price=report_data.get('posts_average_price', 'N/A'),
        users_change=report_data.get('users_change', '0%'),
        vips_change=report_data.get('vips_change', '0%'),
        posts_change=report_data.get('posts_change', '0%'),
    )

    # Correcting file path for saving the report
    file_name = f"report_{date.today()}.html"
    reports_path = root / "reports"
    reports_path.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists
    file_path = reports_path / file_name
    
    async with aiofiles.open(file_path, mode='w') as file:
        await file.write(filled_html)
    
    print(f"Report generated and saved to {file_path}")
    return str(file_path)  # Return the full path as a string