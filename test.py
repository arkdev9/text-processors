from app.utils.fcm import send_message

reg_id = 'dZsOl3ESi4jb6pqMb1hG1V:APA91bFoX_eKJm7AK3sDngdAuW_QlnAbZkj_6RLDgVM5BcU_P17afQurxImlJkoxzFk0gHPO9_jFua3qkMTyufGuL-mqHT751lQFEcSkJTTr2azbkjpUl-0ufh0Zd0M5JgKXl0LeHrKz'

send_message(reg_token=reg_id, title="Transcription didn't complete",
             body="Your transcription wasn't successful", data={'ok': str(False)})
