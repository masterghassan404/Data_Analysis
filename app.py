import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from numerize.numerize import numerize
import plotly.express as px
import mysql.connector
import bcrypt
from mysql.connector import Error
from streamlit_extras.metric_cards import style_metric_cards
import io
import kaleido
import os
import openpyxl
from openpyxl.chart import PieChart, Reference, BarChart

# إعداد الاتصال بقاعدة البيانات
def create_connection():
    return mysql.connector.connect(
        host='localhost',
        port="3306",
        user="root",
        passwd="", 
        database='login'
    )

# دالة لقراءة بيانات العملاء
def read_customer_data():
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers ORDER BY id ASC")  
        data = cursor.fetchall()
        df = pd.DataFrame(data, columns=["EEID", "FullName", "JobTitle", "Department", "BusinessUnit", "Gender", "Ethnicity", "Age", "HireDate", "AnnualSalary", "Bonus", "Country", "City", "id"])
        return df
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# دالة لقراءة بيانات المستخدمين
def read_data():
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, phone, email FROM users")
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=['Name', 'Phone', 'Email'])
        return df
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# دالة لتسجيل الدخول
def login(email, password):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if user:
            stored_password = user[4]
            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                st.success("تم تسجيل الدخول بنجاح!")  
                st.session_state['email'] = email
                st.session_state['logged_in'] = True
            else:
                st.error("كلمة المرور غير صحيحة.")
        else:
            st.error("البريد الإلكتروني غير مسجل.")
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# دالة لإنشاء حساب جديد
def create_account(name, phone, email, password):
    if not name or not phone or not email or not password:
        st.error("يرجى ملء جميع الحقول.")
        return

    try:
        conn = create_connection()
        cursor = conn.cursor()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute("INSERT INTO users (name, phone, email, password) VALUES (%s, %s, %s, %s)", 
                       (name, phone, email, hashed_password))
        conn.commit()
        st.success("تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول.")
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# دالة لعرض بيانات العملاء مع تصفية
def display_customer_data():
    df = read_customer_data()
    
    if df is not None and not df.empty:
        st.subheader("بيانات العملاء")
        
        # تصفية البيانات
        department = st.sidebar.multiselect("تصفية حسب القسم", options=df["Department"].unique(), default=df["Department"].unique())
        country = st.sidebar.multiselect("تصفية حسب البلد", options=df["Country"].unique(), default=df["Country"].unique())
        businessunit = st.sidebar.multiselect("تصفية حسب وحدة الأعمال", options=df["BusinessUnit"].unique(), default=df["BusinessUnit"].unique())
        Gender = st.sidebar.multiselect("تصفية حسب الجنس", options=df["Gender"].unique(), default=df["Gender"].unique()) 

        # تطبيق الفلاتر
        df_selection = df.query("Department in @department & Country in @country & BusinessUnit in @businessunit & Gender in @Gender")

        # اختيار الأعمدة لعرضها
        shwdata = st.multiselect("اختر الأعمدة لعرضها:", options=df.columns.tolist(), default=["EEID", "FullName", "JobTitle", "Department", "BusinessUnit", "Gender", "Ethnicity", "Age", "HireDate", "AnnualSalary", "Bonus", "Country", "City", "id"])

        st.dataframe(df_selection[shwdata], use_container_width=True)

        # زر لحفظ البيانات كملف CSV
        if st.button("حفظ البيانات كملف CSV"):  
            csv = df_selection[shwdata].to_csv(index=False).encode('utf-8')
            st.download_button("تحميل CSV", csv, "data.csv", "text/csv", key='download-csv')

        # زر لحفظ البيانات كملف Excel
        if st.button("حفظ البيانات كملف Excel"):
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df_selection[shwdata].to_excel(writer, index=False, sheet_name='Data')
            excel_buffer.seek(0)
            st.download_button("تحميل Excel", excel_buffer, "data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key='download-excel')
          


        # رسم الرسوم البيانية
        metrics(df_selection)
        pie(df_selection)
        bar(df_selection)

     

    else:
        st.warning("لا توجد بيانات لعرضها.")

       
def load_css():
    with open('style.css') as f:
      st.markdown(f"<style>{f.read()}</style>",unsafe_allow_html=True)


# دالة لعرض المستخدمين
def view_users():
    st.subheader("قائمة المستخدمين")
    df = read_data()
    if df is not None and not df.empty:
        st.dataframe(df)  
    else:
        st.warning("لا توجد بيانات لعرضها.")

# دالة لمخطط دائري
def pie(df_selection):
    fig = px.pie(df_selection, values='AnnualSalary', names='Department', title='Customers by Department')
    fig.update_layout(legend_title="Department", legend_y=0.9)
    fig.update_traces(textinfo="percent+label", textposition='inside')
    st.plotly_chart(fig, use_container_width=True)

# دالة لمخطط عمودي
def bar(df_selection):
    fig = px.bar(df_selection, y="AnnualSalary", x="Department", text_auto='.2s', title="Simple Bar Graph")
    fig.update_traces(textfont_size=10, textangle=0, textposition="outside", cliponaxis=False)
    st.plotly_chart(fig, use_container_width=True)

# دالة لعرض المقاييس
def metrics(df_selection):
    col1, col2, col3 = st.columns(3)
    col1.metric(label="إجمالي العملاء", value=df_selection['Gender'].count(), delta="عدد العملاء")
    col2.metric(label="إجمالي الراتب السنوي", value=f"{df_selection['AnnualSalary'].sum():,.0f}", delta="إجمالي الرواتب")
    col3.metric(label="فرق الراتب السنوي", value=f"{df_selection['AnnualSalary'].max() - df_selection['AnnualSalary'].min():,.0f}", delta="أقصى راتب") 
    style_metric_cards(background_color="golden", border_left_color="#00ff0", box_shadow="3px")



# الدالة الرئيسية
def main():
    load_css()
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        with st.sidebar:
            selected = st.selectbox("اختر خيارًا", ["Create an Account", "Login"])
        
        if selected == "Login":
            st.subheader("تسجيل الدخول")
            email = st.text_input("البريد الإلكتروني", value=st.session_state.get('email', ''))
            password = st.text_input("كلمة المرور", type='password', value=st.session_state.get('password', ''))

            if st.button("دخول"):
                if not email or not password:
                    st.error("يرجى ملء جميع الحقول.")
                else:
                    login(email, password)

        elif selected == "Create an Account":
            st.subheader("إنشاء حساب")
            name = st.text_input("الاسم", value=st.session_state.get('name', ''))
            phone = st.text_input("رقم الهاتف", value=st.session_state.get('phone', ''))
            email = st.text_input("البريد الإلكتروني", value=st.session_state.get('email', ''))
            password = st.text_input("كلمة المرور", type='password', value=st.session_state.get('password', ''))
            
            if st.button("إنشاء حساب"):
                create_account(name, phone, email, password)
    else:
        with st.sidebar:
            selected = st.selectbox("اختر خيارًا", ["View Users", "Customers"])

        if selected == "View Users":
            view_users()
        elif selected == "Customers":
            display_customer_data()

if __name__ == "__main__":
    main()


