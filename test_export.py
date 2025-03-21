import requests

def test_export():
    """Test export functionality"""
    # Login as admin to get token
    login_data = {
        'email': 'admin@iitm.ac.in',
        'password': 'pass'
    }
    
    # Get auth token
    response = requests.post('http://localhost:5000/', json=login_data)
    if not response.ok:
        print("Login failed")
        return
        
    token = response.json()['access_token']
    headers = {'Authentication-Token': token}
    
    # Test export endpoint
    response = requests.post(
        'http://localhost:5000/api/export/users',
        headers=headers
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")

if __name__ == "__main__":
    test_export()