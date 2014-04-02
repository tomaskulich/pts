# imports {{{
import sqlalchemy.ext.declarative
from sqlalchemy import Table, Column, Integer, ForeignKey
from threading import Thread
from time import sleep
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    String,
    Enum,
    DateTime,
    Boolean,
    orm,
    create_engine,
    func,
    )
from sqlalchemy.types import (
    Float,
    TEXT,
    String,
    Date,
    )
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship, backref, joinedload, subqueryload, subqueryload_all
import random
import datetime
import logging
import time
#}}}

def get_random_name(): #{{{
    spol = 'nmptvks'*2+'bzclr'
    sam = 'aeiouy'
    lett = (spol, sam)
    length = random.randint(4,7)
    name = [random.choice(lett[i%2]) for i in range(length)]
    return ''.join(name).capitalize()
#}}}

# schema definition {{{
Base = sqlalchemy.ext.declarative.declarative_base()

person_department = Table('person_department', Base.metadata,
    Column('person_id', Integer, ForeignKey('person.id')),
    Column('dep_id', Integer, ForeignKey('dep.id'))
)


class Person(Base):
    def __init__(self, sid=None, name=None, role=None):
        if sid:
            self.sid=sid
        if name:
            self.name=name
        if role:
            self.role=role

    __tablename__ = 'person'
    id = Column(Integer, primary_key=True)
    sid = Column(Integer)
    name = Column(String)
    role_enum = ENUM('student', 'professor', 'employee', 'other', name = 'role_enum')
    role = Column('role', role_enum, default = 'other')
    deps = relationship('Department', secondary = person_department, backref = 'persons', cascade = 'save-update')

    def __repr__(self):
        return "Person(%s, %s, %s)" % (str(self.id), str(self.sid), str(self.name))


class Department(Base):

    __tablename__='dep'

    def __init__(self, name=None):
        if name:
            self.name=name
    id = Column(Integer, primary_key = True)
    name = Column(String)

    def __repr__(self):
        return "Department(%s, %s)" % (str(self.id), str(self.name))

class Entry(Base):
    __tablename__='entry'
    def __init__(self, date=None):
        if date:
            self.date=date
    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    person_id = Column(Integer, ForeignKey('person.id'))
    #person = relationship("Person", backref = backref('entries', cascade="all, delete-orphan"))
    person = relationship("Person", backref = backref('entries', cascade="all"))
    dep_id = Column(Integer, ForeignKey('dep.id'))
    dep = relationship("Department", backref = backref('entries', cascade="all, delete-orphan"))
    def __repr__(self):
        return "Entry(%s, %s, %s)" % (str(self.id), str(self.person_id), str(self.dep_id))
#}}}

# schema creation {{{
n = 100 
all_persons = []
all_deps = []
engine = create_engine("postgresql+psycopg2://postgres:@/university")
Session = orm.sessionmaker(bind = engine)
session = Session(autoflush = False)

#logging.basicConfig()
hdlr = logging.StreamHandler()
formatter = logging.Formatter('%(message)s')
hdlr.setFormatter(formatter)
logger = logging.getLogger('sqlalchemy.engine')
logger.addHandler(hdlr)

#}}}

logger.setLevel(logging.WARNING)
#logger.setLevel(logging.INFO)

def recreate(): #{{{
    """
    recreates the whole db structure: departments, persons, entries, department-person relationship
    """
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    for i in range(4*n):
        p = Person(name = get_random_name(), 
                   sid = random.randint(10**5,10**6), 
                   role = random.choice(['student', 'professor', 'other']))
        all_persons.append(p)
        session.add(p)
        
    for i in range(n):
        dep = Department(name = 'department of ' + get_random_name())
        all_deps.append(dep)
        session.add(dep)

    for i in range(20*n):
        random.choice(all_persons).deps.append(random.choice(all_deps))

    for i in range(n*n):
        now = datetime.datetime.today()
        onesec = datetime.timedelta(seconds = 1)
        entry = Entry(date = now - onesec * random.randint(0, 365*24*3600))
        entry.person = random.choice(all_persons)
        entry.dep = random.choice(all_deps)
        session.add(entry)

    session.commit()
#}}}

#recreate()

def basic_operations(): #{{{
    person = session.query(Person).filter(Person.id == 1).one()
    print(person)
    person.name = 'fero'
    print(person)
    print(person.deps)
    person.deps[0].name = 'ferov depp'
    print(person.deps) #}}}

#basic_operations()

def adding_data(): #{{{
    person = Person(name = 'jozo', role = 'student')
    session.add(person)
    dep = Department(name = 'jozov dep')
    person.deps.append(dep)
    print(person, person.deps)
    session.commit()
    print(person, person.deps)
#}}}

#adding_data()

def deleting_person_dont_cascade(): #{{{
    person = session.query(Person).filter(Person.id == 1).one()
    print(person)
    print(person.deps)
    deps_ids = [dep.id for dep in person.deps]
    session.delete(person)
    deps = session.query(Department).filter(Department.id.in_(deps_ids)).all()
    print(deps)
#}}}

#deleting_person_dont_cascade()

def deleting_person_cascade(): #{{{
    person = session.query(Person).filter(Person.id == 1).one()
    print(person)
    print(len(person.entries), person.entries)
    print('---')
    entry_ids = [entry.id for entry in person.entries]
    #session.delete(person)
    person.entries.pop(0)
    print(len(person.entries), person.entries)
    print('---')
    session.flush()
    entries = session.query(Entry).filter(Entry.id.in_(entry_ids)).all()
    print(len(entries), entries)
    print('---')
#}}}

#deleting_person_cascade()

def ex_identity_map(): #{{{
    person = session.query(Person).filter(Person.id == 1).one()
    print('@'*50)
    print(person)
    for i in range(100):
        person.name = 'fero_' + str(i)
    person.name = 'fero'
    person = session.query(Person).filter(Person.id == 1).one()
    print('@'*50)
    print(person)
    person = session.query(Person).filter(Person.name == 'Mine').first()
    print('@'*50)
    print(person)
#}}}

#ex_identity_map()

def ex1(): #{{{
    print('\n\n\n')
    person = session.query(Person).filter(Person.id==1).one()
    #entries=session.query(Entry).filter(Entry.person==person).all()
    entries = person.entries
    print('@'*50)
    print(person)
    print(entries)
    entries_ids = [entry.id for entry in entries]
    session.delete(person)
    entries = session.query(Entry).filter(Entry.id.in_(entries_ids)).all()
    print('@'*50)
    print(entries)
#}}}


def lazy_vs_subquery(): #{{{
    print('\n'*30)
    #person = session.query(Person).first()
    #for entry in person.entries:
    #    print(entry.dep)
    #print("@"*100)
    #session.expunge_all()
    #persons = session.query(Person).\
    #  filter(Person.name.like("%a%")).\
    #  options(joinedload(Person.entries)).all()
    #print('\n'.join([str((person, person.entries[0])) for person in persons]))
      #options(joinedload_all(Person.entries, Entry.dep)).all()
    persons = session.query(Person).filter(Person.name.like("%a%")).options(subqueryload_all(Person.entries, Entry.dep)).all()
    print([(person, person.entries[0].dep) for person in persons])
#}}}

#lazy_vs_subquery()

def get_time(f): #{{{
    def res(*args):
        start=time.time()
        f(*args)
        end=time.time()
        print("time: "+str(end-start))
    return res
#}}}

# complex query {{{
@get_time 
def complex_query():
    """ hidden comment #{{{
    create index c on entry (person_id)
    create index c on entry (person_id, date)
    #}}} """ 
    for person in session.query(Person).all():
        session.query(Entry).filter(Entry.person_id == person.id).order_by(Entry.date).first()
#}}}

complex_query()

def session_merge(): #{{{
    person = session.query(Person).filter(Person.id==1).one()
    print(person)
    session.expunge(person)
    person.name='Fero'
    session.flush()
    print('before merge')
    session.merge(person)
    person = session.query(Person).filter(Person.id==1).one()
    session.flush()
    print(person)
#}}}

#session_merge()

def aggregate(): #{{{
    res = session.query(Entry.person_id, func.count('*').label('entries_count')).group_by(Entry.person_id).all()
    for _id, count in res:
        print(_id, count)
#}}}

#aggregate()
