import os
import requests
import json
from typing import Any, Text, Dict, List, Union, Optional
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormAction
from rasa_sdk.types import DomainDict
from dotenv import load_dotenv

load_dotenv()

airtable_api_key=os.getenv("AIRTABLE_API_KEY")
base_id=os.getenv("BASE_ID")
table_name=os.getenv("TABLE_NAME")

def create_health_log(
  confirm_exercise, 
  exercise, 
  sleep, 
  diet, 
  stress, 
  goal):
  
  request_url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
  headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": f"Bearer {airtable_api_key}"
    
  }
  data = {
    "fields": {
      "Exercised?": confirm_exercise,
      "Type of exercise": exercise,
      "Amount of sleep": sleep,
      "Stress": stress,
      "Diet": diet,
      "Goal": goal
    }  
  }
  try:
    resp = requests.post(
      request_url,
      headers=headers, 
      data=json.dumps(data))
    resp.raise_for_status()
  except requests.exceptions.HTTPError as err:
    raise SystemExit(err)

  print(resp.status_code)
  return resp
  

class ValidateHealthForm(FormValidationAction):
  
  def name(self):
    return "validate_health_form"

  async def required_slots(
    self,
    slots_mapped_in_domain: List[Text],
    dispatcher: CollectingDispatcher,
    tracker: Tracker,
    domain: DomainDict,
  ) -> Optional[List[Text]]:
    #print("[SLOTS]", tracker.slots) 
    #print("[REQUESTED]", tracker.slots.get('requested_slot'))
    #print("[LAST_ACT]", tracker.latest_action_name)
    #print("[LTST_MSG]", tracker.get_intent_of_latest_message())
    #if tracker.get_intent_of_latest_message() == "out_of_scope":
    #  tracker.slots['requested_slot'] = None
    #  print(" [UPD_REQUESTED]", tracker.slots.get('requested_slot'))
    if tracker.slots.get("confirm_exercise") == True:
      return ["confirm_exercise", "exercise", "sleep", "diet", "stress", "goal"]
    else:
      return ["confirm_exercise", "sleep", "diet", "stress", "goal"]
   
  def extract_confirm_exercise(
    self,
    dispatcher: CollectingDispatcher,
    tracker: Tracker,
    domain: Dict
  ) -> Dict[Text, Any]:
    
    if (not tracker.slots.get('requested_slot') == "confirm_exercise" or tracker.get_last_event_for(event_type="action", exclude=["health_form"], skip=1)['name'] == "utter_ask_continue"):
      return {}
      
    intent = tracker.latest_message['intent'].get('name')
    if intent == "affirm" or intent == "inform":
      return { "confirm_exercise": True }
    elif intent == "deny":
      return { "confirm_exercise": False }
    else:
      return {}

  async def extract_sleep(
    self,
    dispatcher: CollectingDispatcher,
    tracker: Tracker,
    domain: Dict
  ) -> Dict[Text, Any]:
     
    if not tracker.slots.get('requested_slot') == 'sleep':
      return {}

    intent = tracker.latest_message['intent'].get('name')
    if intent == "deny":
      return { "sleep": "None" }
    else:
      return {}

    entities = tracker.latest_message.get('entities')
    for entity in entities:
      if entity['entity'] == "sleep":
        return { "sleep": entity['value'] }
    return {} 

      
  async def extract_diet(
    self,
    dispatcher: CollectingDispatcher,
    tracker: Tracker,
    domain: Dict
  ) -> Dict[Text, Any]:
 
    if not tracker.slots.get('requested_slot') == "diet":
      return {}
      
    intent = tracker.latest_message['intent'].get('name')
    if intent == "affirm" or intent == "inform" or intent == "deny":
      return { "diet": tracker.latest_message.get('text') }
    else:
      return {}

  async def extract_goal(
    self,
    dispatcher: CollectingDispatcher,
    tracker: Tracker,
    domain: Dict
  ) -> Dict[Text, Any]:
    
    if not tracker.slots.get('requested_slot') == 'goal':
      return {}

    intent = tracker.latest_message['intent'].get('name')
    if intent == "inform":
      return { "goal": tracker.latest_message.get('text') }
    else:
      return {}


class SubmitFormAction(Action):
  
  def name(self) -> Text:
    return "action_submit_form"

  async def run(
    self,
    dispatcher,
    tracker: Tracker,
    domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
    response = create_health_log(
      tracker.get_slot("confirm_exercise"),
      tracker.get_slot("exercise"),
      tracker.get_slot("sleep"),
      tracker.get_slot("stress"),
      tracker.get_slot("diet"),
      tracker.get_slot("goal")
    )
    
    dispatcher.utter_message("Thanks! Your answers have been recorded!")

    return []
  
