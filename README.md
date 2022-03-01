# UCAS_script
Adapted from [WuYunfan/UCAS_course_script](https://github.com/WuYunfan/UCAS_course_script)


⚠️ **Due to the update of the site validation mechanism, the current version is no longer suitable.**

It will be updated someday. (mainly because we are too lazy...)

(The scheme is very simple, that is, the identification(s) of the verification code and course selection submission need to be updated.)



**Warning: Only postgraduate courses are supported.**


## Instructions
1. For the first use, you need to download resources from here and place them in the root directory.

   https://drive.google.com/file/d/1QsWvbpxFKPfCiZlfDZY5PsDwjyenEtrU/view?usp=sharing

   **Verification code recognition technology provided by XuanBaoBao.**

2. Refer to "config_sample.json" to create a new configuration file named "config.json" and fill in account information and course information. (You can view the source code on the course selection page to get the labels (deptId), if you don’t specify it, it will automatically select all). Moreover, if you need email notification, fill in your mailbox in "receivers".

   For example:

   > {
   >  "username" : "xxxx",
   >  "password" : "xxxx",
   >  "courses" : ["070100M01003H"],
   >  "labels": ["910"],
   >  "receivers": ["xxxxxxxxx@xxx.com"]
   > }

3. Install dependencies
  ```
  pip install -r requirements.txt
  ```

4. Run the program.
  ```
  python script1.py
  ```
