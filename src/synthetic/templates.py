# Template dialogue blocks for synthetic transcripts (EN/ES).
# Keys: persona, language, then trait or segment (greeting/body/closing).
# Each value is a list of (speaker, text) for turns.

COLLECTIONS_EN = {
    "greeting_full": [
        ("agent", "Thank you for calling Premier Auto Finance, this is Sarah. May I have your name please?"),
        ("customer", "Yes, this is James Miller."),
        ("agent", "Thank you, Mr. Miller. This is an attempt to collect a debt. Any information will be used for that purpose. Can you confirm the last four of your social and your date of birth so I can pull up your account?"),
        ("customer", "Sure, it's 4522 and DOB 03-15-1985."),
        ("agent", "Thank you, I've verified you. How can I help you today?"),
    ],
    "greeting_no_miranda_no_rpv": [
        ("agent", "Premier Auto Finance, this is Sarah."),
        ("customer", "Hi, I'm calling about my account."),
        ("agent", "Sure, what's the account number? I'll pull it up."),
        ("customer", "It's 789234."),
        ("agent", "I see you're past due by 45 days. The balance is $2,400. We need to get this resolved."),
    ],
    "greeting_ok": [
        ("agent", "Thank you for calling Premier Auto Finance, this is Sarah. Who do I have the pleasure of speaking with?"),
        ("customer", "James Miller."),
        ("agent", "Thank you. Can you confirm last four of social and date of birth for security?"),
        ("customer", "4522, 03-15-85."),
        ("agent", "Thanks. I have your account. How can I help?"),
    ],
    "body_accurate_recap": [
        ("customer", "I want to set up a payment plan."),
        ("agent", "I can offer a payment arrangement. Your current past-due amount is $800. We can do two payments of $400 due on the 15th and 30th. Would that work?"),
        ("customer", "Yes."),
        ("agent", "I'll note two payments of $400, first due on the 15th and second on the 30th. You'll receive a confirmation. Is there anything else?"),
        ("customer", "No, that's it."),
        ("agent", "Just to confirm: we've set up two payments of $400, on the 15th and 30th. Please make sure they're made on time to avoid further action. Thank you for calling Premier Auto Finance. Have a good day."),
    ],
    "body_no_recap": [
        ("customer", "I can pay $400 next week."),
        ("agent", "I can set that up. So $400 next week. Anything else?"),
        ("customer", "No."),
        ("agent", "Thanks for calling. Bye."),
    ],
    "body_aggressive": [
        ("agent", "You're 45 days past due. We need payment now or we're sending this to repossession. What are you going to do?"),
        ("customer", "I'm trying to work with you."),
        ("agent", "Then pay. When? Today?"),
        ("customer", "I can do $400 Friday."),
        ("agent", "Fine. Friday. Don't miss it."),
    ],
    "body_wrong_balance": [
        ("agent", "Your balance is $2,100 and we need it paid."),
        ("customer", "I thought it was $1,900."),
        ("agent", "It's $2,100. Let's get it taken care of."),
    ],
    "body_third_party_promises": [
        ("agent", "Premier Auto Finance, Sarah speaking."),
        ("customer", "Hi, I'm calling for my brother, he's at work. Can you tell me what he owes?"),
        ("agent", "Sure, what's his name and account number? I can look it up and see what we can do for him. I might be able to waive some fees if he calls back by Friday."),
    ],
    "closing_recap": [
        ("agent", "To confirm: two payments of $400 on the 15th and 30th. You'll get a confirmation. Thank you for calling Premier Auto Finance. Have a good day."),
    ],
    "closing_none": [],
}

COLLECTIONS_ES = {
    "greeting_full": [
        ("agent", "Gracias por llamar a Premier Auto Finance, soy María. ¿Me da su nombre por favor?"),
        ("customer", "Sí, soy Carlos Rodríguez."),
        ("agent", "Gracias, Sr. Rodríguez. Esta es una comunicación para cobrar una deuda. ¿Puede confirmar los últimos cuatro de su seguro social y su fecha de nacimiento para verificar su cuenta?"),
        ("customer", "Claro, 8899 y 20 de mayo de 1980."),
        ("agent", "Gracias, ya lo verifiqué. ¿En qué puedo ayudarle hoy?"),
    ],
    "greeting_no_miranda_no_rpv": [
        ("agent", "Premier Auto Finance, con María."),
        ("customer", "Hola, llamo por mi cuenta."),
        ("agent", "¿Cuál es el número de cuenta?"),
        ("customer", "456123."),
        ("agent", "Veo que tiene 45 días de atraso. El saldo es $2,400. Hay que resolver esto."),
    ],
    "greeting_ok": [
        ("agent", "Gracias por llamar a Premier Auto Finance, soy María. ¿Con quién hablo?"),
        ("customer", "Carlos Rodríguez."),
        ("agent", "¿Puede confirmar los últimos cuatro del seguro social y fecha de nacimiento?"),
        ("customer", "8899, 20 de mayo del 80."),
        ("agent", "Gracias. Tengo su cuenta. ¿En qué puedo ayudarle?"),
    ],
    "body_accurate_recap": [
        ("customer", "Quiero hacer un plan de pagos."),
        ("agent", "Puedo ofrecerle un arreglo. El monto vencido es $800. Podemos hacer dos pagos de $400 los días 15 y 30. ¿Le funciona?"),
        ("customer", "Sí."),
        ("agent", "Quedan dos pagos de $400, el 15 y el 30. Recibirá una confirmación. ¿Algo más?"),
        ("customer", "No."),
        ("agent", "Para confirmar: dos pagos de $400, el 15 y el 30. Gracias por llamar a Premier Auto Finance. Que tenga buen día."),
    ],
    "body_no_recap": [
        ("customer", "Puedo pagar $400 la próxima semana."),
        ("agent", "Puedo anotarlo. $400 la próxima semana. ¿Algo más?"),
        ("customer", "No."),
        ("agent", "Gracias por llamar. Adiós."),
    ],
    "body_aggressive": [
        ("agent", "Tiene 45 días de atraso. Necesitamos el pago ya o enviamos a recuperación. ¿Qué va a hacer?"),
        ("customer", "Estoy tratando de cooperar."),
        ("agent", "Entonces pague. ¿Cuándo? ¿Hoy?"),
        ("customer", "Puedo dar $400 el viernes."),
        ("agent", "Bien. El viernes. No falle."),
    ],
    "closing_recap": [
        ("agent", "Para confirmar: dos pagos de $400 los días 15 y 30. Recibirá confirmación. Gracias por llamar a Premier Auto Finance. Que tenga buen día."),
    ],
    "closing_none": [],
}

RAM_EN = {
    "greeting_full": [
        ("agent", "Hi, this is Chris with Premier Auto Finance RAM. Who am I speaking with?"),
        ("dealer", "This is Mike at Riverside Chevrolet."),
        ("agent", "Thanks, Mike. Can you confirm your dealer ID so I pull up the right account?"),
        ("dealer", "Sure, it's RIV-789."),
        ("agent", "Got it. How can I help you today?"),
    ],
    "greeting_ok": [
        ("agent", "Premier Auto Finance RAM, this is Chris."),
        ("dealer", "Hi, Mike from Riverside."),
        ("agent", "Thanks, Mike. What do you need?"),
    ],
    "body_portal_recap": [
        ("dealer", "I'm stuck on the portal, can't find where to upload the stips."),
        ("agent", "No problem. Go to Dealer Central, then Applications, then the application number. You'll see a link that says Upload Documents. Click that and add the stips one by one. Did that work?"),
        ("dealer", "Yes, I see it."),
        ("agent", "Great. So next steps: finish uploading the stips, then hit Submit. Underwriting typically reviews within 2 business days. If anything's missing we'll reach out. You have my number if you need anything else."),
    ],
    "body_no_recap": [
        ("dealer", "Where do I upload stips?"),
        ("agent", "Dealer Central, Applications, then your app number. There's an Upload Documents link."),
        ("dealer", "Got it."),
        ("agent", "Okay, bye."),
    ],
    "body_overpromise": [
        ("dealer", "When will this get approved?"),
        ("agent", "We'll have it done by end of day today, no problem."),
        ("dealer", "Great."),
        ("agent", "Yeah, you're all set. Bye."),
    ],
    "body_wrong_docs_bypass": [
        ("dealer", "Can I skip the proof of insurance for now?"),
        ("agent", "Yeah, sometimes we can work around that. Just submit the rest and we'll see."),
        ("dealer", "And the income doc?"),
        ("agent", "Underwriting usually wants it but we've made exceptions. Try without and we'll let you know."),
    ],
    "body_contradict_uw": [
        ("dealer", "Your underwriting said LTV has to be under 120%."),
        ("agent", "They say that but we've approved higher. Push it through and we'll take a look."),
    ],
    "closing_recap": [
        ("agent", "So to summarize: upload the stips in Dealer Central under your app, then submit. We'll review within 2 business days. You have my number. Thanks, Mike."),
    ],
    "closing_none": [],
}

RAM_ES = {
    "greeting_full": [
        ("agent", "Hola, soy Laura de Premier Auto Finance RAM. ¿Con quién hablo?"),
        ("dealer", "Soy Pedro de Concesionario Norte."),
        ("agent", "Gracias, Pedro. ¿Me confirma su ID de concesionario?"),
        ("dealer", "NORTE-456."),
        ("agent", "Listo. ¿En qué puedo ayudarle?"),
    ],
    "greeting_ok": [
        ("agent", "Premier Auto Finance RAM, con Laura."),
        ("dealer", "Hola, Pedro de Concesionario Norte."),
        ("agent", "Gracias, Pedro. ¿Qué necesita?"),
    ],
    "body_portal_recap": [
        ("dealer", "No encuentro dónde subir los documentos en el portal."),
        ("agent", "Vaya a Centro del Concesionario, Aplicaciones, luego el número de su aplicación. Verá un enlace Subir documentos. Ahí sube los stip. ¿Le apareció?"),
        ("dealer", "Sí."),
        ("agent", "Próximos pasos: suba los stip y luego Enviar. Suscripción revisa en unos 2 días hábiles. Si falta algo le contactamos. Tiene mi número. ¿Algo más?"),
    ],
    "body_no_recap": [
        ("dealer", "¿Dónde subo los stip?"),
        ("agent", "Centro del Concesionario, Aplicaciones, su app. Ahí está Subir documentos."),
        ("dealer", "Listo."),
        ("agent", "De acuerdo. Adiós."),
    ],
    "body_overpromise": [
        ("dealer", "¿Cuándo lo aprueban?"),
        ("agent", "Para hoy mismo lo tenemos, sin problema."),
        ("dealer", "Perfecto."),
        ("agent", "Sí, quedó. Adiós."),
    ],
    "body_wrong_docs_bypass": [
        ("dealer", "¿Puedo omitir el seguro por ahora?"),
        ("agent", "A veces se puede. Envíe el resto y vemos."),
        ("dealer", "¿Y el comprobante de ingresos?"),
        ("agent", "Suscripción suele pedirlo pero ha habido excepciones. Pruebe sin eso."),
    ],
    "closing_recap": [
        ("agent", "Resumen: suba los stip en Centro del Concesionario y envíe. Revisamos en 2 días hábiles. Tiene mi número. Gracias, Pedro."),
    ],
    "closing_none": [],
}


def get_templates(persona: str, language: str) -> dict:
    if persona == "collections" and language == "en":
        return COLLECTIONS_EN
    if persona == "collections" and language == "es":
        return COLLECTIONS_ES
    if persona == "ram" and language == "en":
        return RAM_EN
    if persona == "ram" and language == "es":
        return RAM_ES
    return COLLECTIONS_EN  # fallback
