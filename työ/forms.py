from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField 
from wtforms.validators import DataRequired, Email, EqualTo, Length

class RegistrationForm(FlaskForm):
    username = StringField(label='Username',validators=[DataRequired(),Length(min=3,max=20),])
    email = StringField(label='Email',validators=[DataRequired(),Email()])
    password = PasswordField(label='Password',validators=[DataRequired(),Length(min=6,max=16)])
    confirm_password = PasswordField(label='Confirm Password',validators=[DataRequired(),EqualTo('password')])
    submit = SubmitField(label='Sign Up')

class LoginForm(FlaskForm):
    email = StringField(label='Email',validators=[DataRequired(),Email()])
    password = PasswordField(label='Password',validators=[DataRequired(),Length(min=6,max=16)])
    
    submit = SubmitField(label='Login')

class PasswordForm(FlaskForm):
    password = PasswordField(label='Password',validators=[DataRequired(),Length(min=6,max=16)])

class ThreadForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Create Thread')

class PostForm(FlaskForm):
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Post')

class AreaForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    is_secret = BooleanField('Secret')
    submit = SubmitField('Create Area')
