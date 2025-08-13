import psycopg2

# Connect to database 
conn = psycopg2.connect(host='localhost', database='painpoint_ai', user='postgres', password='Jiraiya@106', port=5432)
cur = conn.cursor()

# Check URL patterns to identify mock vs real data
print('🔍 ANALYZING DATA SOURCE...')
print('=' * 60)

# Count URLs with 'realistic' pattern (mock data)
cur.execute("SELECT COUNT(*) FROM fetched_problems WHERE url LIKE '%realistic%'")
mock_count = cur.fetchone()[0]

# Count URLs with actual reddit.com pattern (real data)  
cur.execute("SELECT COUNT(*) FROM fetched_problems WHERE url LIKE '%reddit.com/r/%' AND url NOT LIKE '%realistic%'")
real_reddit_count = cur.fetchone()[0]

# Total count
cur.execute('SELECT COUNT(*) FROM fetched_problems')
total_count = cur.fetchone()[0]

print(f'📊 DATA BREAKDOWN:')
print(f'   Total entries: {total_count}')
print(f'   Mock/sample data ("realistic" URLs): {mock_count}') 
print(f'   Real Reddit data: {real_reddit_count}')
print(f'   Other: {total_count - mock_count - real_reddit_count}')
print()

# Show sample of each type
if mock_count > 0:
    print('🎭 SAMPLE MOCK DATA:')
    cur.execute("SELECT title, url, reddit_id FROM fetched_problems WHERE url LIKE '%realistic%' LIMIT 3")
    for title, url, reddit_id in cur.fetchall():
        print(f'   • {title[:50]}...')
        print(f'     URL: {url}')
        print(f'     ID: {reddit_id}')
        print()

if real_reddit_count > 0:
    print('🌐 SAMPLE REAL REDDIT DATA:')
    cur.execute("SELECT title, url, reddit_id FROM fetched_problems WHERE url LIKE '%reddit.com/r/%' AND url NOT LIKE '%realistic%' LIMIT 3")
    for title, url, reddit_id in cur.fetchall():
        print(f'   • {title[:50]}...')
        print(f'     URL: {url}')
        print(f'     ID: {reddit_id}')
        print()

# Final assessment
print('🎯 CONCLUSION:')
if mock_count == total_count:
    print('   ALL DATA IS MOCK/SAMPLE DATA')
    print('   These are realistic-looking examples created for demonstration')
elif real_reddit_count > 0:
    print('   MIXED DATA: Contains both real Reddit data and mock examples')
else:
    print('   DATA SOURCE UNCLEAR: No obvious mock or Reddit patterns found')

cur.close()
conn.close()
    