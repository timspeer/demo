Here is a sample of my most recent projects.

I do not use a separated project/program model, instead everything works as though it were in the same project.
I did not want to constantly update the same module in multiple places so each project pull from a common folder,
which then pulls from the Globals folders.

So the general logic is as follows:

Globals => common => import

I have included a sample of some of the most relevant work I have done.  I have removed any network information
and replaced it with #REMOVED#


**Accounting Scripts:

I have included a class that calls on an API to upload files to a Citrix service we use.  It is called from
the backen of my Django site.

**Custom Report

I have included a sample of an SQL call that is converted into a Dataframe and then into a csv where it is
uploaded to a third party via an API.

**Django

I have included some of the code for my Django site that is most relevant to showing my skills.

**Reconcile

I have included a program that pulls all sources of input data and enters them into an SQL table where it is used 
in the Django site.

**SFTP Transfer and File Setup

This directory has the most information about how I take data and put it into our SQL server.
I have included three specific examples:

    /mtrx_evergreen - XML
    /pcfc_chi - PDFs
    /vall_vmc - CSV

**Stored Procedures

I have copied down two of my most relevant stored procedures.  One fixes data in the SQL with some very minor
machine learning logic.  The other finds and compares records between our production program and my custom work.

**Sweep

I have included samples of some of my API work to pull down files on a set schedule.

**Web Scraping

For many of our Clients, I use Selenium to automate downloading pdfs.  I include this because it is a very useful
tool for testing website and I am well versed in it.



--I have not included much of my common network interfacing programs, because they are more IT relevant and are
probably not of particular interest here.


-Thank you for your time.