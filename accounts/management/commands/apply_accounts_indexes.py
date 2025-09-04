"""
Auto-apply Accounts module database indexes during deployment
This command runs automatically via Dockerfile
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Apply Accounts module production indexes automatically'
    
    def handle(self, *args, **options):
        if connection.vendor != 'postgresql':
            self.stdout.write('Skipping Accounts indexes (not PostgreSQL)')
            return
        
        self.stdout.write('👥 Applying Accounts module indexes...')
        
        indexes = [
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_accounts_user_email ON accounts_user (email);", 
             "User email index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_accounts_user_groups ON accounts_user_groups (user_id, group_id);", 
             "User groups index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_accounts_user_active ON accounts_user (is_active, date_joined);", 
             "User active status index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_accounts_teammember_type_active ON accounts_teammember (team_type, is_active, \"order\");", 
             "TeamMember type and order index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_accounts_teammember_search ON accounts_teammember USING gin(to_tsvector('english', name || ' ' || position));", 
             "TeamMember full-text search index"),
        ]
        
        success_count = 0
        for sql, desc in indexes:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(sql)
                self.stdout.write(f"✅ {desc}")
                success_count += 1
            except Exception as e:
                self.stdout.write(f"⚠️  {desc} - {str(e)}")
        
        self.stdout.write(f'👥 Accounts indexes: {success_count}/{len(indexes)} applied')
