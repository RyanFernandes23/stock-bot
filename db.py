import redis
import json
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class RedisDB:
    def __init__(self):
        self.r = redis.Redis(
    host='redis-13702.c11.us-east-1-2.ec2.redns.redis-cloud.com',
    port=13702,
    decode_responses=True,
    username="default",
    password=os.getenv("REDIS_PASSWORD"),
)




    
    def create_user(self, username, password, role, assigned_analyst=None):
        user_key = f"user:{username}"
        if self.r.exists(user_key):
            return False
        
        user_data = {
            'password': password,
            'role': role,
            'assigned_analyst': assigned_analyst or ''
        }
        self.r.hset(user_key, mapping=user_data)
        return True
    
    def authenticate_user(self, username, password):
        user_key = f"user:{username}"
        if not self.r.exists(user_key):
            return False
        
        stored_password = self.r.hget(user_key, 'password')
        return stored_password == password
    
    def get_user_role(self, username):
        user_key = f"user:{username}"
        return self.r.hget(user_key, 'role')
    
    def get_assigned_analyst(self, investor_username):
        user_key = f"user:{investor_username}"
        return self.r.hget(user_key, 'assigned_analyst')
    
    def get_investors_for_analyst(self, analyst_username):
        investors = []
        for key in self.r.keys('user:*'):
            user_data = self.r.hgetall(key)
            if user_data.get('assigned_analyst') == analyst_username:
                investors.append(key.split(':')[1])
        return investors
    
    def save_report(self, analyst, investor, stock, analysis, action, allocation):
        report_id = str(uuid.uuid4())
        report_key = f"report:{report_id}"
        
        report_data = {
            'id': report_id,
            'analyst': analyst,
            'investor': investor,
            'stock': stock,
            'date': str(datetime.now()),
            'analysis': json.dumps(analysis),
            'action': action,
            'allocation': str(allocation)
        }
        
        self.r.hset(report_key, mapping=report_data)
        
        # Add to investor's report list
        self.r.lpush(f"reports:{investor}", report_id)
        return report_id
    
    def get_reports(self, username):
        report_ids = self.r.lrange(f"reports:{username}", 0, -1)
        reports = []
        for report_id in report_ids:
            report_key = f"report:{report_id}"
            report = self.r.hgetall(report_key)
            if report:
                reports.append(report)
        return reports

# Initialize database connection
db = RedisDB()