$password = Read-Host "Enter your MySQL root password"

@"
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=$password
MYSQL_DATABASE=hostelfix
MYSQL_PORT=3306
SECRET_KEY=hostelfix-local-secret
"@ | Set-Content -Encoding UTF8 -Path ".env"

Write-Host ""
Write-Host ".env file created successfully."
Write-Host "Now restart Flask with: python app.py"
