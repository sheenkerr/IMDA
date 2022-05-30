from xmlrpc.client import Boolean, boolean
from fastapi import FastAPI, Request, Form, status, HTTPException
from typing import Optional,List
from numpy import double
import pandas as pd
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.sql.expression import func
from pydantic import BaseModel

import models
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

templates = Jinja2Templates(directory="templates")


db = SessionLocal()
class RamenReviews(BaseModel): 
    ID:Optional[int]
    Country:str 
    Brand:str 	
    Type:str 
    Package:str 
    Rating:double
    Complete:Optional[Boolean]
    
    class Config:
        orm_mode=True
 

country_df = pd.read_csv('Country-Codes.csv')
fullCountryList = country_df.Country.tolist()
fullCountryCodeList = country_df.Code.tolist()
packageList = ["Bar","Bowl","Box","Can","Cup","Pack","Tray"]

def get_latest_ID( ):
    db_ID=db.query(func.max(models.RamenReviews.ID)).scalar()
    return db_ID


# Check for empty stirng
def is_empty(string):
	return not string.strip()

def check_valid_input(review):
    if (float(review.Rating) > 5 or float(review.Rating) < 0):
        return "Please Ensure the Rating is in the ranges of 0 to 5 (inclusive)"
    elif is_empty(review.Country):
        return "Please ensure the Country field is not left blank"
    elif (not (review.Country in fullCountryList or (review.Country.upper() in fullCountryCodeList))):
        return "Please enter a valid country name or Alpha-3 Country Code"
    elif is_empty(review.Brand):
        return "Please Ensure the Brand field is not left blank"
    elif is_empty(review.Type):
        return "Please Ensure the Type field is not left blank"    
    elif is_empty(review.Package):
        return "Please Ensure the Package field is not left blank" 
    elif (not (review.Package in packageList)):
        return "Please enter a valid Package (" + ", ".join(packageList) + ")" 
    
    return ""

# Maps Alpha-3 Code to Country
def map_code_to_country(code):
    if(country_df[country_df["Code"] == code.upper()].Country.to_string(index=False).strip()[:6] != 'Series'):
        return country_df[country_df["Code"] == code.upper()].Country.to_string(index=False).strip()
    return ""


# API REST Endpoints
#===========================================================================================================
# Get all Reviews
@app.get("/reviews",response_model=List[RamenReviews],status_code=200)
def get_all_reviews( ):
    reviews = db.query(models.RamenReviews).all()
    return reviews
    

# Get Specfic Review by ID
@app.get('/review/{review_id}',response_model=RamenReviews,status_code=status.HTTP_200_OK)
def get_a_review(review_id:int ):
    review=db.query(models.RamenReviews).filter(models.RamenReviews.ID==review_id).first()
    if(review == None):
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND,detail="No Review Found")
    return review


 # Search by Text or by if review is complete or not 
@app.get("/search_review")
def search_review(Country: str = "", Brand: str = "",  Type: str = "", Package: str = "", Rating: float = None, Complete: boolean = None):
    # Prevent Empty Search
    if (is_empty(Country + Type + Brand + Package) and Complete ==None and Rating == None):
        raise HTTPException(status_code=400,detail="Please Ensure that at least one of the fields (Country, Brand, Type, Package, Complete, Rating) are not blank to perform a search")
    if(len(Country)==3): # Check using Alpha-3 Code
        Country = map_code_to_country(Country)

    # If user indicated if they want to see complete or uncomplete reviews with a particular rating
    if(Complete != None and Rating !=None):
        reviews=db.query(models.RamenReviews).filter(models.RamenReviews.Country.contains(Country),models.RamenReviews.Brand.contains(Brand),models.RamenReviews.Type.contains(Type),models.RamenReviews.Package.contains(Package),models.RamenReviews.Complete == Complete,models.RamenReviews.Rating == Rating).all()
    # If user indicated if they want to see complete or uncomplete reviews without a particular rating
    elif(Complete != None and Rating ==None):
        reviews=db.query(models.RamenReviews).filter(models.RamenReviews.Country.contains(Country),models.RamenReviews.Brand.contains(Brand),models.RamenReviews.Type.contains(Type),models.RamenReviews.Package.contains(Package),models.RamenReviews.Complete == Complete).all()
   
    # If user did not indicated if they want to see complete or uncomplete reviews with  a particular rating
    elif(Complete == None and Rating !=None):
        reviews=db.query(models.RamenReviews).filter(models.RamenReviews.Country.contains(Country),models.RamenReviews.Brand.contains(Brand),models.RamenReviews.Type.contains(Type),models.RamenReviews.Package.contains(Package),models.RamenReviews.Rating == Rating).all()
    
    # If user did not indicated if they want to see complete or uncomplete reviews (Shows Both Complete and Uncomplete)
    else:
        reviews=db.query(models.RamenReviews).filter(models.RamenReviews.Country.contains(Country),models.RamenReviews.Brand.contains(Brand),models.RamenReviews.Type.contains(Type),models.RamenReviews.Package.contains(Package)).all()
 
    if reviews == []:
         raise HTTPException(status_code = status.HTTP_404_NOT_FOUND,detail="No Review Found")
    return reviews
      
       
# Add Review
@app.post('/review',response_model=RamenReviews,
        status_code=status.HTTP_201_CREATED)
def create_a_review(review:RamenReviews):
    
    # Error checking for if the user leave any one of the required fields blank or rating not between 0 and 5
    validity = check_valid_input(review)
    country = review.Country
    if(len(validity)==0):  # No Problems found
        if(len(review.Country) ==3):
            country = map_code_to_country(review.Country)
            if(country == ""):
                 raise HTTPException(status_code=400,detail="Please enter a valid country name or Alpha-3 Country Code")
            
        new_review=models.RamenReviews(
            ID = get_latest_ID() + 1,
            Country  = country,
            Brand = review.Brand,
            Type = review.Type,
            Package = review.Package,
            Rating = review.Rating,
            Complete = 1        
            )
        db.add(new_review)
        db.commit()

        return new_review
        
    else:
        raise HTTPException(status_code=400,detail=validity)
    

# Update review by ID
@app.put('/review/{review_id}',response_model=RamenReviews,status_code=status.HTTP_200_OK)
def update_review(review_id:int,review:RamenReviews):
    review_to_update=db.query(models.RamenReviews).filter(models.RamenReviews.ID==review_id).first()
    
    if review_to_update is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Review Found")
    
      # Error checking for if the user leave any one of the required fields blank or rating not between 0 and 5
    validity = check_valid_input(review)
    
    country = review.Country
    if(len(validity)==0):  # No Problems found
        if(len(review.Country) ==3):
            country = map_code_to_country(review.Country)
            print(country)
            if(country == ""):
                    raise HTTPException(status_code=400,detail="Please enter a valid country name or Alpha-3 Country Code")

        
        review_to_update.Brand = review.Brand
        review_to_update.Country = country
    
        review_to_update.Type = review.Type
    
        review_to_update.Package = review.Package
    
        review_to_update.Rating = review.Rating    
        review_to_update.Complete = 1    

      
        db.commit()
        
        
        return review_to_update 
    
        
    else:
        raise HTTPException(status_code=400,detail=validity)
    
   
# Delete
@app.delete('/review/{review_id}')
def delete_review(review_id:int, ):
    review_to_delete=db.query(models.RamenReviews).filter(models.RamenReviews.ID==review_id).first()
    if review_to_delete is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Review Found")
    
    db.delete(review_to_delete)
    db.commit()

    return review_to_delete


#==================================================================================================================
# Web App

def get_list_of_countries(reviewsList):
    uniqueCountryList = []
      
    # traverse for all elements
    for review in reviewsList:
        # check if exists in unique_list or not
        if review.Country not in uniqueCountryList:
            uniqueCountryList.append(review.Country)

    return sorted(uniqueCountryList)

# Home Page
@app.get("/",response_model=List[RamenReviews],status_code=200)
def home(request: Request):
    reviews = db.query(models.RamenReviews).filter(models.RamenReviews.Complete == True).all()
    uniqueCountryList = get_list_of_countries(reviews)
    
    return templates.TemplateResponse("base.html",
                                      {"request": request, "reviews_list": reviews,"country_list": uniqueCountryList})

# Add Review Page Render
@app.get("/add",response_model=List[RamenReviews],status_code=200)
def home(request: Request):
        
    return templates.TemplateResponse("Add.html",
                                      {"request": request,"country_list": fullCountryList})

#Add new review
@app.post("/add")
def add_review(Country: str = Form(...),Brand: str = Form(...), Type: str = Form(...),Package: str = Form(...), Rating: str = Form(...) ):
	
    new_review=models.RamenReviews(
            ID = get_latest_ID() + 1,
            Country  = Country,
            Brand = Brand,
            Type = Type,
            Package = Package,
            Rating = Rating,
            Complete = 1        
            )
    db.add(new_review)
    db.commit()

    url = app.url_path_for("home")
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)

#Update Existing Review
@app.get("/update/{rating_id}")
def update_review(request: Request, rating_id: int):
    review = db.query(models.RamenReviews).filter(models.RamenReviews.ID == rating_id).first()
    fullCountryListUpdate = fullCountryList.copy()
    fullCountryListUpdate.remove(review.Country)
    
    packageListUpdate = packageList.copy()
    packageListUpdate.remove(review.Package)
    db.commit()
       
    return templates.TemplateResponse("Update.html",
                                      {"request": request, "review": review,"country_list":fullCountryListUpdate,"packageList":packageListUpdate})
    
@app.post("/update/{rating_id}")
def update_review(rating_id: int,  Country: str = Form(...),Brand: str = Form(...), Type: str = Form(...),Package: str = Form(...), Rating: str = Form(...)):
    review = db.query(models.RamenReviews).filter(models.RamenReviews.ID == rating_id).first()
    review.Country = Country
    review.Brand = Brand
    review.Type = Type
    review.Package = Package
    review.Rating = Rating
    review.Complete = 1

    db.commit()
       
    url = app.url_path_for("home")
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)

# Delete Review
@app.get("/delete/{rating_id}")
def delete_review(rating_id: int, ):
    rating = db.query(models.RamenReviews).filter(models.RamenReviews.ID == rating_id).first()
    db.delete(rating)
    db.commit()
    url = app.url_path_for("home")
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)