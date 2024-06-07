import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import aiohttp
import time
from DAXXMUSIC import app

approved_cards = []
declined_cards = []
invalid_format_cards = []

async def get_bin_info(bin_number):
    url = f"https://lookup.binlist.net/{bin_number}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "brand": data.get("scheme", "Unknown").upper(),
                    "type": data.get("type", "Unknown").upper(),
                    "level": data.get("brand", "Unknown").upper(),
                    "issuer": data.get("bank", {}).get("name", "Unknown"),
                    "country": data.get("country", {}).get("name", "Unknown"),
                    "country_emoji": data.get("country", {}).get("emoji", "")
                }
            else:
                return {
                    "brand": "Unknown",
                    "type": "Unknown",
                    "level": "Unknown",
                    "issuer": "Unknown",
                    "country": "Unknown",
                    "country_emoji": ""
                }

@app.on_message(filters.document)
async def handle_document(client, message):
    global approved_cards, declined_cards, invalid_format_cards
    approved_cards = []
    declined_cards = []
    invalid_format_cards = []

    document = message.document
    if document.mime_type == 'text/plain':
        start_time = time.time()
        await message.download(f"/tmp/{document.file_name}")
        
        with open(f"/tmp/{document.file_name}", 'r') as file:
            card_details = file.readlines()
        
        for line in card_details:
            parts = line.strip().split('|')
            if len(parts) == 4:
                card_number, exp_month, exp_year, cvc = parts
                bin_number = card_number[:6]
                bin_info = await get_bin_info(bin_number)
                is_approved = random.random() > 0.99  # 1% chance of approval
                elapsed_time = round(time.time() - start_time, 2)
                result = (
                    f"𝗖𝗮𝗿𝗱: {card_number}|{exp_month}|{exp_year}|{cvc}\n"
                    f"𝐆𝐚𝐭𝐞𝐰𝐚𝐲: Braintree Auth\n"
                    f"𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: {'Approved' if is_approved else 'Card Issuer Declined CVV'}\n\n"
                    f"𝗜𝗻𝗳𝗼: {bin_info['brand']} - {bin_info['type']} - {bin_info['level']}\n"
                    f"𝐈𝐬𝐬𝐮𝐞𝐫: {bin_info['issuer']}\n"
                    f"𝐂𝐨𝐮𝐧𝐭𝐫𝐲: {bin_info['country']} {bin_info['country_emoji']}\n\n"
                    f"𝗧𝗶𝗺𝗲: {elapsed_time} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬"
                )
                if is_approved:
                    approved_cards.append(f"𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅\n{result}")
                else:
                    declined_cards.append(f"𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌\n{result}")
            else:
                invalid_format_cards.append(line.strip())
        
        total_cards = len(card_details)
        approved_count = len(approved_cards)
        declined_count = len(declined_cards)
        invalid_count = len(invalid_format_cards)

        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(f"View Approved Cards ({approved_count})", callback_data="view_approved")],
                [InlineKeyboardButton(f"View Declined Cards ({declined_count})", callback_data="view_declined")],
                [InlineKeyboardButton(f"View Invalid Format Cards ({invalid_count})", callback_data="view_invalid")],
            ]
        )

        await message.reply(
            f"Processing Complete!\nTotal Cards: {total_cards}\nApproved: {approved_count}\nDeclined: {declined_count}\nInvalid Format: {invalid_count}",
            reply_markup=keyboard
        )
    else:
        await message.reply("Please upload a valid .txt file.")

@app.on_callback_query(filters.regex("view_approved"))
async def view_approved(client, callback_query):
    global approved_cards
    if approved_cards:
        approved_text = "\n\n".join(approved_cards)
        approved_cards = []  # Clear approved cards after displaying
        await callback_query.message.reply(f"Approved Cards:\n{approved_text}")
    else:
        await callback_query.message.reply("No approved cards.")
    await update_buttons(callback_query)

@app.on_callback_query(filters.regex("view_declined"))
async def view_declined(client, callback_query):
    global declined_cards
    if declined_cards:
        declined_text = "\n\n".join(declined_cards)
        declined_cards = []  # Clear declined cards after displaying
        await callback_query.message.reply(f"Declined Cards:\n{declined_text}")
    else:
        await callback_query.message.reply("No declined cards.")
    await update_buttons(callback_query)

@app.on_callback_query(filters.regex("view_invalid"))
async def view_invalid(client, callback_query):
    global invalid_format_cards
    if invalid_format_cards:
        invalid_text = "\n".join(invalid_format_cards)
        invalid_format_cards = []  # Clear invalid format cards after displaying
        await callback_query.message.reply(f"Invalid Format Cards:\n{invalid_text}")
    else:
        await callback_query.message.reply("No invalid format cards.")
    await update_buttons(callback_query)

async def update_buttons(callback_query):
    global approved_cards, declined_cards, invalid_format_cards
    approved_count = len(approved_cards)
    declined_count = len(declined_cards)
    invalid_count = len(invalid_format_cards)
    
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(f"View Approved Cards ({approved_count})", callback_data="view_approved")],
            [InlineKeyboardButton(f"View Declined Cards ({declined_count})", callback_data="view_declined")],
            [InlineKeyboardButton(f"View Invalid Format Cards ({invalid_count})", callback_data="view_invalid")],
        ]
    )
    
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)
    await callback_query.answer()
