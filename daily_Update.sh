#!/bin/bash

# Navigate to the project directory
cd /home/abhishekyadav/WORK/TEST/SOS/Gemini/JavaQuestions || exit

# Add a new update with the current timestamp
echo "Update on $(date '+%Y-%m-%d %H:%M:%S')" >> updates.txt

# Run the Python script
/usr/bin/python3 /home/abhishekyadav/WORK/TEST/SOS/Gemini/test.py >> /home/abhishekyadav/WORK/Github/daily_update.log 2>&1


# Configure Git and commit changes
git add .
git config --global user.name "Abhishek Yadav"
git config --global user.email "abhishekyadav17012000@gmail.com"
git commit -m "Updated for new problem statement: $(date '+%Y-%m-%d')"
git push origin main