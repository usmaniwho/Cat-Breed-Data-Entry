# TODO - Cat Data Entry Task

## Task: Make changes so that it does NOT keep data from previous sessions. Only access data if CSV is uploaded in Current Data Tab, and delete previous session data.

### Steps to Complete:

- [x] 1. Add code at app start to delete any existing CSV files from previous sessions (cat_data.csv, cat_data_uploaded.csv)
- [x] 2. Keep the file upload feature to access data ONLY when a new CSV is uploaded in the Current Tab
- [x] 3. After uploading and displaying data, clear the CSV file so it's not kept for next session
- [x] 4. Modify data entry to NOT persist to CSV (just keep in memory for current session only)

### Implementation Plan:
1. Delete previous session CSV files on app startup using os.remove()
2. Allow CSV upload only for current session viewing
3. Clear CSV after display to prevent persistence to next session
4. Use Streamlit session state to keep data in memory only (no CSV persistence)

### Testing:
- [x] Test that page refresh clears all previous data
- [x] Test that uploading CSV shows data only in current session
- [x] Test that data entry doesn't persist after refresh
