def test_homepage(client):
    response = client.get("/")
    
    assert response.status_code == 200
    assert b"Exam" in response.data
