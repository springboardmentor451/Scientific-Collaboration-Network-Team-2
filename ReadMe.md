# Structure 
                              SciCollab
                                  │
                 ┌────────────────┴────────────────┐
                 │                                 │
          RESEARCHER PANEL                    ADMIN PANEL
                 │                                 │
     ┌───────────┼───────────┐          ┌──────────┼──────────┐
     │           │           │          │          │          │
 Dashboard   My Profile  My Work     Dashboard   User       Master
     │           │           │          Management Data
     │           │           │                     │
     │           │      ┌────┼────┐       ┌────────┼─────────────┐
     │           │      │    │    │       │        │             │
     │           │  Publications  │   Researchers Institutions Publications
     │           │               │       │        │             │
     │           │          Conferences │   Conferences       Collaborations
     │           │          Collaborations│
     │           │          Analytics     │
     │           │          Notifications │
     │           │          Settings      │
     │           │                        │
     └───────────┴────────────────────────┘




     # Admin panel   

     ADMIN PANEL
│
├── Dashboard
│
├── User Management
│   ├── All Users
│   ├── Researchers
│   ├── Admins
│   └── Account Status
│
├── Institution Management
│   ├── Institutions
│   ├── Add Institution
│   └── Edit Institution
│
├── Publication Management
│   ├── All Publications
│   ├── Pending
│   └── Approved
│
├── Conference Management
│   ├── All Conferences
│   ├── Add Conference
│   └── Participants
│
├── Collaboration Management
│   ├── All Collaborations
│   ├── Active
│   ├── Pending
│   └── Completed
│
├── Analytics
│
├── Notifications
│
├── Settings
│
└── Profile  

# Researcher panel  

RESEARCHER PANEL
│
├── Dashboard
│
├── Researchers
│   └── View Research Network
│
├── My Publications
│
├── Conferences
│   └── Browse / Participate
│
├── My Collaborations
│
├── Analytics
│
├── Notifications
│
├── Settings
│
├── Profile
│
└── Logout


# architecture 

                    ┌──────────────────┐
                    │      LOGIN       │
                    └────────┬─────────┘
                             │
                      Check user.role
                             │
              ┌──────────────┴──────────────┐
              │                             │
        role=researcher                 role=admin
              │                             │
              ▼                             ▼
     Researcher Dashboard           Admin Dashboard
              │                             │
       Limited permissions          Full management
              │                             │
              └──────────────┬──────────────┘
                             │
                     Common Services
                             │
              ┌──────────────┼──────────────┐
              │              │              │
           FastAPI       PostgreSQL       Auth

           