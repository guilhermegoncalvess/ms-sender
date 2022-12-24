import logging
from concurrent import futures
from google.cloud import pubsub_v1
import smtplib
import json

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logging.basicConfig(level=logging.INFO)

project_id = "learning-357114"
subscription_id = 'order-sub'
# project_id = "your-project-id"
# subscription_id = "test-subscription"

subscriber = pubsub_v1.SubscriberClient()
# The `subscription_path` method creates a fully qualified identifier
# in the form `projects/{project_id}/subscriptions/{subscription_id}`
subscription_path = subscriber.subscription_path(project_id, subscription_id)

def callback(message):
    logging.info("Received %s", json.loads(message.data))
    content = json.loads(message.data)
    gmail_user = 'guilhermegufes@gmail.com'
    gmail_password = 'nrsuwyofoypgrkkg'

    sent_from = gmail_user
    to = content['user']['email']

    email_text = MIMEMultipart("alternative")
    email_text["Subject"] = "Pedido Realizado!"
    email_text["From"] = sent_from
    email_text["To"] = to
    
    table = ''
    for item in content['products']:
        td=f"""\
            <span style="display:block;font-size:14px;line-height:20px;margin-bottom:5px">
                <strong>{item['name']}</strong>
            </span>   
            <span> 
                <div style="line-height:22px">  
                    Descrição: {item['description']}<br>     
                </div> 
                <span> 
                    Quantidade: {item['quantity']}
                </span><br> 
                <span style="line-height:22px"> 
                    Valor do produto: R$ <strong>{item['quantity']*item['value']}</strong><br> 
                </span> 
            </span> <br>
       
        """

        table = table + td

    text = f"""\
    Olá {content['user']['name']},
    Seu pedido foi recebido com sucesso!"""
    html = f"""\
    <html>
    <body>
        <div><strong>{text}</strong></div><br>
        <table width="100%" border="0" style="background:#f5f5f5;font-family:Trebuchet ms,Arial,sans-serif;font-size:14px;margin-bottom:10px" >
            <tr>
                <h3>Número do pedido</h3>
                {content['_id']}<br>
                <td width="70%" style="color:#666;padding:20px"> <p style="color:#666;font-size:14px;line-height:20px;margin:0;padding:0;padding-bottom:20px"> 
                {table}

                <p><strong>Valor total da compra: {content['totalPrice']}</strong></p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    # part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    
    # email_text.attach(part1)
    email_text.attach(part2)

    try:
        smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        smtp_server.ehlo()
        smtp_server.login(gmail_user, gmail_password)
        smtp_server.sendmail(sent_from, to, email_text.as_string())
        smtp_server.close()
        print (f"Email sent successfully to {to}.")
    except Exception as ex:
        print ("Something went wrong….",ex)
    
    message.ack()
    return message

future = subscriber.subscribe(subscription_path, callback=callback)

with subscriber:
    try:
        future.result()
    except futures.TimeoutError:
        future.cancel()  # Trigger the shutdown.
        future.result()  # Block until the shutdown is complete.


