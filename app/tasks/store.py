import asyncio
import logging
import os
import secrets
import traceback
from PIL import Image
from tasks.admin import AsyncSessionFactory
from tasks.configs import celery_app
from crud.posts import crud_post
from crud.users import crud_user
from datetime import datetime

@celery_app.task
def upload_picture(file_content: bytes, filename: str, dir: str):
    extension = filename.split(".")[-1].lower()
    if extension not in ["jpg", "png"]:
        return "File extension must be .jpg or .png"

    token_name = secrets.token_hex(10) + "." + extension
    generated_name = os.path.join(dir, token_name)

    # Save the file
    try:
        with open(generated_name, "wb") as out_file:
            out_file.write(file_content)
    except Exception as e:
        return f"Error saving file: {str(e)}"

    # Process the image
    try:
        with Image.open(generated_name) as img:
            img = img.resize((512, 512))
            img.save(generated_name)
    except Exception as e:
        return f"Error processing image: {str(e)}"

    # Assume all paths involve 'static/' for simplicity
    file_url = generated_name.split("static/")[1]
    return file_url


@celery_app.task(name='update_post_vip_from_user_vip')
def update_product_vip_task():
    async def update_product_vip():
        async with AsyncSessionFactory() as session:
            try:
                users = await crud_user.get_multi(session)
                
                for user in users:
                    posts = await crud_post.get_multi_filtered(session, owner=user.id)
                    
                    for post in posts:
                        await crud_post.update(session, obj_in={'is_vip': user.is_vip})
            except Exception as e:
                logging.error(f"Error during post vip status changing: {e}\n{traceback.format_exc()}")
            finally:
                await session.close()  # Ensure the session is closed
        try:
            asyncio.run(update_product_vip())
        except Exception as e:
                logging.critical(f"Error during post vip status chanching task starting: {e}\n{traceback.format_exc()}")



@celery_app.task(name='unvip_exited_users')
def unvip_exited_users():
    async def perfom_unvip():
        async with AsyncSessionFactory() as session:
            try:
                users = await crud_user.get_multi_filtered(session, is_vip=True)
                
                for user in users:
                    
                    if user.viped_at <  datetime.today():
                    
                        await crud_user.update(session, obj_in={'is_vip': True,
                                                                'viped_at': None })
                       
            except Exception as e:
                logging.error(f"Error during unviping: {e}\n{traceback.format_exc()}")
            finally:
                await session.close()  # Ensure the session is closed
    try:
        asyncio.run(perfom_unvip())
    except Exception as e:
        logging.critical(f"Error during unviping task starting: {e}\n{traceback.format_exc()}")
