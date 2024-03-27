from pydantic import BaseModel


class DailyReportScheme(BaseModel):
    total_users: int
    total_activated: int
    total_posts: int
    total_vips: int
    new_users: int
    new_posts: int
    new_vips: int
    users_change: str
    posts_change: str
    vips_change: str
    posts_average_price: float
