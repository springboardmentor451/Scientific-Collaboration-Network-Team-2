--
-- PostgreSQL database dump
--

\restrict YwIbxMifGzmh2bNchKudf8UJQ0mb7Y9k6ts1jNmReDBInR4II41f6dmJQV7KBlG

-- Dumped from database version 16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: collaboration_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.collaboration_type AS ENUM (
    'CO_AUTHORSHIP',
    'JOINT_PROJECT',
    'INSTITUTIONAL_PARTNERSHIP',
    'OTHER'
);


--
-- Name: participation_role; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.participation_role AS ENUM (
    'PRESENTER',
    'ATTENDEE',
    'ORGANIZER',
    'REVIEWER'
);


--
-- Name: project_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.project_status AS ENUM (
    'PLANNED',
    'ACTIVE',
    'ON_HOLD',
    'COMPLETED',
    'CANCELLED'
);


--
-- Name: publication_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.publication_status AS ENUM (
    'DRAFT',
    'SUBMITTED',
    'PUBLISHED',
    'ARCHIVED'
);


--
-- Name: publication_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.publication_type AS ENUM (
    'JOURNAL_PAPER',
    'CONFERENCE_PAPER',
    'BOOK',
    'PATENT',
    'TECHNICAL_REPORT',
    'OTHER'
);


--
-- Name: tag_category; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.tag_category AS ENUM (
    'SKILL',
    'RESEARCH_INTEREST'
);


--
-- Name: user_role; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.user_role AS ENUM (
    'RESEARCHER',
    'INSTITUTION_ADMIN',
    'REVIEWER',
    'SYSTEM_ADMIN'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_logs (
    id uuid NOT NULL,
    user_id uuid,
    action character varying(100) NOT NULL,
    entity_type character varying(100) NOT NULL,
    entity_id character varying(100),
    details jsonb,
    ip_address character varying(45),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: citations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.citations (
    id uuid NOT NULL,
    citing_publication_id uuid NOT NULL,
    cited_publication_id uuid,
    external_title character varying(500),
    external_doi character varying(255),
    external_authors character varying(500),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_citation_has_target CHECK (((cited_publication_id IS NOT NULL) OR (external_title IS NOT NULL)))
);


--
-- Name: collaborations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.collaborations (
    id uuid NOT NULL,
    collaboration_type public.collaboration_type NOT NULL,
    institution_a_id uuid,
    institution_b_id uuid,
    project_id uuid,
    start_date date,
    end_date date,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: conference_participations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conference_participations (
    id uuid NOT NULL,
    conference_id uuid NOT NULL,
    researcher_id uuid NOT NULL,
    publication_id uuid,
    role public.participation_role NOT NULL,
    presentation_title character varying(500),
    registered_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: conferences; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conferences (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    location character varying(255),
    website character varying(255),
    start_date date,
    end_date date,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: institutions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.institutions (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    country character varying(100),
    address text,
    website character varying(255),
    institution_type character varying(100),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: project_members; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_members (
    project_id uuid NOT NULL,
    researcher_id uuid NOT NULL,
    role character varying(100) NOT NULL,
    joined_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: projects; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.projects (
    id uuid NOT NULL,
    title character varying(300) NOT NULL,
    description text,
    funding_source character varying(255),
    budget numeric(14,2),
    status public.project_status NOT NULL,
    start_date date,
    end_date date,
    lead_institution_id uuid,
    lead_researcher_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: publication_authors; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.publication_authors (
    publication_id uuid NOT NULL,
    researcher_id uuid NOT NULL,
    author_order integer NOT NULL,
    is_corresponding boolean NOT NULL
);


--
-- Name: publications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.publications (
    id uuid NOT NULL,
    title character varying(500) NOT NULL,
    abstract text,
    publication_type public.publication_type NOT NULL,
    status public.publication_status NOT NULL,
    doi character varying(255),
    journal_or_venue character varying(255),
    volume character varying(50),
    issue character varying(50),
    pages character varying(50),
    publication_date date,
    file_path character varying(500),
    project_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: researcher_tags; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.researcher_tags (
    researcher_id uuid NOT NULL,
    tag_id uuid NOT NULL
);


--
-- Name: researchers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.researchers (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    institution_id uuid,
    full_name character varying(255) NOT NULL,
    department character varying(150),
    academic_title character varying(100),
    orcid_id character varying(25),
    bio text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: tags; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tags (
    id uuid NOT NULL,
    name character varying(100) NOT NULL,
    category public.tag_category NOT NULL
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    email character varying(255) NOT NULL,
    hashed_password character varying(255) NOT NULL,
    role public.user_role NOT NULL,
    is_active boolean NOT NULL,
    is_verified boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alembic_version (version_num) FROM stdin;
6186495bcc36
\.


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.audit_logs (id, user_id, action, entity_type, entity_id, details, ip_address, created_at) FROM stdin;
\.


--
-- Data for Name: citations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.citations (id, citing_publication_id, cited_publication_id, external_title, external_doi, external_authors, created_at) FROM stdin;
e6a4709c-0222-4f65-9fad-98d5d6afea10	f001239a-86d6-42c5-9cef-e80a71bbaa2b	dd03b49e-9179-4b4f-9f4c-43ccc4f58480	\N	\N	\N	2026-08-14 18:11:01.310566+00
b4b1957a-34d7-4df4-bf2d-dc54acd0363a	f001239a-86d6-42c5-9cef-e80a71bbaa2b	dd4dafa6-23d4-44b8-88fc-54a480e0f779	\N	\N	\N	2026-08-14 18:11:01.310566+00
24e36885-dd17-4e0f-b2cf-9cb33d138420	f001239a-86d6-42c5-9cef-e80a71bbaa2b	a1c6b4e3-f162-49a1-97a6-137291fddbf7	\N	\N	\N	2026-08-14 18:11:01.310566+00
3ea8e301-2acd-439f-98ca-2fec99ec9281	a1c6b4e3-f162-49a1-97a6-137291fddbf7	\N	Something others someone nature country think join economic resource position stock	10.3979/b6f005c3	Bobby Garrett	2026-08-14 18:11:01.310566+00
855016a3-2dd7-4c5c-be7c-df1730462897	a1c6b4e3-f162-49a1-97a6-137291fddbf7	87df24d8-6606-4e0a-a5fd-1d3bb0ba57d2	\N	\N	\N	2026-08-14 18:11:01.310566+00
2a6b872a-b0d8-4f5a-8a0e-aec770f9d468	a1c6b4e3-f162-49a1-97a6-137291fddbf7	\N	Share travel space range expect sea speak include table consumer face PM	10.6576/ccb784f5	Denise Dean	2026-08-14 18:11:01.310566+00
f0411c3b-3194-43e3-9eb0-8c67ee92a181	00fc5533-b42d-4719-929f-5c7274281df1	\N	Fly charge wide against win example by just	10.5526/58923f29	Brandon Smith	2026-08-14 18:11:01.310566+00
0e24e2b2-6398-4b08-bfae-2dff2e2cbf88	00fc5533-b42d-4719-929f-5c7274281df1	0d5dcfcb-ea96-4a41-81ae-74b9504667a3	\N	\N	\N	2026-08-14 18:11:01.310566+00
222a950d-27c4-4244-a458-3033e8e07a28	c0d5d015-8261-405f-9c5b-02d890d1ccde	b647712f-9cd9-41a4-955d-3949cc3120ea	\N	\N	\N	2026-08-14 18:11:01.310566+00
2b538e0e-b837-48dd-87e5-11bc07badc7a	6be5b5ef-f84d-4b49-aa84-ce493ba0c2cd	b52bae1b-4310-4b87-8c83-1e5fff7dc509	\N	\N	\N	2026-08-14 18:11:01.310566+00
87f01c98-24f5-4e72-9821-3acf60fd2c35	6be5b5ef-f84d-4b49-aa84-ce493ba0c2cd	\N	Game find son your less social form such	10.9041/21d2535a	Amy Rowe	2026-08-14 18:11:01.310566+00
1d947b18-fddd-408e-9536-b324840f462e	6be5b5ef-f84d-4b49-aa84-ce493ba0c2cd	f001239a-86d6-42c5-9cef-e80a71bbaa2b	\N	\N	\N	2026-08-14 18:11:01.310566+00
86a806dc-93ef-469e-b64f-18949a0096a8	c26ffc3f-1959-4153-8324-98713f7f80e0	6f7aa5ed-0a13-4a84-8493-7875e1e5c28d	\N	\N	\N	2026-08-14 18:11:01.310566+00
4a6c1e2c-0a60-412a-b01b-74401bb89833	c26ffc3f-1959-4153-8324-98713f7f80e0	dd4dafa6-23d4-44b8-88fc-54a480e0f779	\N	\N	\N	2026-08-14 18:11:01.310566+00
59abac54-4104-4645-b327-36e9fcbfa2a8	ca41832d-5e7c-426d-a4be-b69a92c46b28	0d5dcfcb-ea96-4a41-81ae-74b9504667a3	\N	\N	\N	2026-08-14 18:11:01.310566+00
12dddd07-f75e-488c-be0a-3d399457a7ec	ca41832d-5e7c-426d-a4be-b69a92c46b28	20490192-eaef-4fcd-95ad-8d4e16d1775c	\N	\N	\N	2026-08-14 18:11:01.310566+00
9b9566d3-2498-42b4-8d6c-3d28a6133e8d	b52bae1b-4310-4b87-8c83-1e5fff7dc509	dd03b49e-9179-4b4f-9f4c-43ccc4f58480	\N	\N	\N	2026-08-14 18:11:01.310566+00
4341c2b1-8205-4aaa-a218-d9a054c21113	b52bae1b-4310-4b87-8c83-1e5fff7dc509	1aa6bf79-065c-4df0-a1b8-1108a163c186	\N	\N	\N	2026-08-14 18:11:01.310566+00
3f8876ab-2bc9-473a-a243-506aeb7dd140	1aa6bf79-065c-4df0-a1b8-1108a163c186	c26ffc3f-1959-4153-8324-98713f7f80e0	\N	\N	\N	2026-08-14 18:11:01.310566+00
ac0a224f-5745-47cf-a600-af0351084660	bcb11c43-ed7f-4e1e-9e84-76eacd0a6e0d	20490192-eaef-4fcd-95ad-8d4e16d1775c	\N	\N	\N	2026-08-14 18:11:01.310566+00
e850d558-6db2-4329-b15e-481bc4f71084	bcb11c43-ed7f-4e1e-9e84-76eacd0a6e0d	\N	Myself consider time economic high actually	10.4033/2d61ace1	Michelle Cruz	2026-08-14 18:11:01.310566+00
d7ffba14-3f9d-4b74-b3da-63db9129a6a6	0507ea92-778e-496b-829f-0b8fada69a1a	f13e9b82-ff81-4683-893c-7d27565709cb	\N	\N	\N	2026-08-14 18:11:01.310566+00
44e29521-f161-4a56-9e6c-90662aa79168	87df24d8-6606-4e0a-a5fd-1d3bb0ba57d2	\N	East yes current same behind program decade home which view city	10.9595/94f281e4	Natasha Dunn	2026-08-14 18:11:01.310566+00
a521c4c3-8b4a-401d-8965-b6eb220cf4b3	87df24d8-6606-4e0a-a5fd-1d3bb0ba57d2	c0d5d015-8261-405f-9c5b-02d890d1ccde	\N	\N	\N	2026-08-14 18:11:01.310566+00
131e8ec6-9e61-4e29-b8da-aa36f879eb95	99c367d9-7330-430c-b9cf-b32fcf189201	0507ea92-778e-496b-829f-0b8fada69a1a	\N	\N	\N	2026-08-14 18:11:01.310566+00
ba58398c-e7f4-4bc3-9ea7-d01b8137e983	b647712f-9cd9-41a4-955d-3949cc3120ea	6f7aa5ed-0a13-4a84-8493-7875e1e5c28d	\N	\N	\N	2026-08-14 18:11:01.310566+00
a89dcbe7-d684-4ad9-b837-c18556ec170c	dd03b49e-9179-4b4f-9f4c-43ccc4f58480	a1c6b4e3-f162-49a1-97a6-137291fddbf7	\N	\N	\N	2026-08-14 18:11:01.310566+00
b47198e3-399b-4bf5-87fe-4f390ff676f1	f13e9b82-ff81-4683-893c-7d27565709cb	\N	Education police cup thought tell design both	10.3068/bf399c90	Erika Jackson	2026-08-14 18:11:01.310566+00
59b63a84-e84e-482c-8f30-c0d8e7a8a05c	f13e9b82-ff81-4683-893c-7d27565709cb	\N	Once how during why ok real read choice side	10.9042/3c3baad3	Jonathan Parks	2026-08-14 18:11:01.310566+00
fe20a9b9-01d7-4c77-996e-bd16343de77e	ff038a64-ba2d-457b-8acf-db733fd9f68e	b647712f-9cd9-41a4-955d-3949cc3120ea	\N	\N	\N	2026-08-14 18:11:01.310566+00
41972eec-91ce-4406-a547-87702a19296b	ff038a64-ba2d-457b-8acf-db733fd9f68e	a1c6b4e3-f162-49a1-97a6-137291fddbf7	\N	\N	\N	2026-08-14 18:11:01.310566+00
ea291135-181b-435f-a9ee-cb5f0f0cb57d	c6a9f531-e79a-458d-8fd6-9d179c8acfcf	\N	Us young personal art popular red social call discussion word	10.8827/8c7de3b4	Nicole Trujillo	2026-08-14 18:11:01.310566+00
7e978d8e-1f6e-4270-a509-b94b5ab212dc	c6a9f531-e79a-458d-8fd6-9d179c8acfcf	00fc5533-b42d-4719-929f-5c7274281df1	\N	\N	\N	2026-08-14 18:11:01.310566+00
955c8e5b-a78d-48ca-a18e-3362fe323c94	2c6330cb-76c8-4f7b-9147-13fdcfdfc038	20490192-eaef-4fcd-95ad-8d4e16d1775c	\N	\N	\N	2026-08-14 18:11:01.310566+00
e91124f9-2b13-4ca5-beb5-24f533e00c32	2c6330cb-76c8-4f7b-9147-13fdcfdfc038	\N	Run again help right economy always religious next my majority note	10.1878/ed843a82	Erica Mcdonald	2026-08-14 18:11:01.310566+00
401bee1a-2f86-402c-8322-b6d2360c16c6	2c6330cb-76c8-4f7b-9147-13fdcfdfc038	20490192-eaef-4fcd-95ad-8d4e16d1775c	\N	\N	\N	2026-08-14 18:11:01.310566+00
68c1e939-3761-4ec2-ae8e-5cd36a1b3694	dd4dafa6-23d4-44b8-88fc-54a480e0f779	ca41832d-5e7c-426d-a4be-b69a92c46b28	\N	\N	\N	2026-08-14 18:11:01.310566+00
4760f3e1-6228-4cac-abae-0f1e639fcefc	dd4dafa6-23d4-44b8-88fc-54a480e0f779	99c367d9-7330-430c-b9cf-b32fcf189201	\N	\N	\N	2026-08-14 18:11:01.310566+00
51210cd3-18e7-4af6-bd57-811256b2cfde	6f7aa5ed-0a13-4a84-8493-7875e1e5c28d	\N	Trial never attention choice fast enjoy happen a point here control affect task	10.7232/a896ea49	Cynthia Le	2026-08-14 18:11:01.310566+00
\.


--
-- Data for Name: collaborations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.collaborations (id, collaboration_type, institution_a_id, institution_b_id, project_id, start_date, end_date, notes, created_at) FROM stdin;
3e97b0b0-8120-4567-87fb-32613d931efe	CO_AUTHORSHIP	e893353b-5e17-4b8e-8f8f-72f84e13be94	542a3fc3-c5b9-4fc6-8b40-156c55077771	\N	2024-07-30	2025-02-21	Pretty show college glass start sort perhaps key.	2026-08-14 18:11:01.310566+00
3fd45691-51e8-4a91-b1e6-efd582f4b85e	JOINT_PROJECT	fe76c92f-e973-45ca-9df1-1c6af7b8a105	fb075e07-3b72-496a-aad5-56344e096cb2	21dc6aea-6a05-4283-bb73-60d306288148	2026-05-22	\N	Current health serious table both.	2026-08-14 18:11:01.310566+00
2e61bba1-c824-4407-943f-9e064daf1fcd	OTHER	e893353b-5e17-4b8e-8f8f-72f84e13be94	fe76c92f-e973-45ca-9df1-1c6af7b8a105	\N	2023-10-12	2025-07-27	Unit than star add really born late age.	2026-08-14 18:11:01.310566+00
8905d306-9d97-4c2a-a69e-cfb434a6588c	JOINT_PROJECT	72e01afd-44ae-43a2-9176-9c9141919ac8	fe76c92f-e973-45ca-9df1-1c6af7b8a105	\N	2024-03-30	\N	Deep national seek nature performance yeah reason.	2026-08-14 18:11:01.310566+00
df376c0e-7a16-41cd-9932-d07673227346	INSTITUTIONAL_PARTNERSHIP	72e01afd-44ae-43a2-9176-9c9141919ac8	fb075e07-3b72-496a-aad5-56344e096cb2	\N	2025-08-15	\N	On professional analysis color exist smile.	2026-08-14 18:11:01.310566+00
51d72b8b-91e5-4e0e-a5cf-3685cd8ba114	INSTITUTIONAL_PARTNERSHIP	e893353b-5e17-4b8e-8f8f-72f84e13be94	542a3fc3-c5b9-4fc6-8b40-156c55077771	\N	2025-06-21	2026-07-21	Let war at.	2026-08-14 18:11:01.310566+00
10ebfb72-e823-4085-aeeb-806135131e1f	OTHER	542a3fc3-c5b9-4fc6-8b40-156c55077771	0b7ee577-5db0-4984-bb45-6a0b6f221a99	\N	2025-08-06	2027-03-14	Ten affect test power discuss herself.	2026-08-14 18:11:01.310566+00
94044b62-8be6-4f9e-9cbf-27beee281e2d	OTHER	e893353b-5e17-4b8e-8f8f-72f84e13be94	0b7ee577-5db0-4984-bb45-6a0b6f221a99	20358546-5b74-4d23-bad4-ef38ec048f1c	2026-07-19	\N	Tough machine others because.	2026-08-14 18:11:01.310566+00
cbfa9b13-b515-44e1-8af3-1255b96659be	OTHER	0b7ee577-5db0-4984-bb45-6a0b6f221a99	72e01afd-44ae-43a2-9176-9c9141919ac8	6988648f-6986-4527-a818-e1ee41d26aba	2024-03-18	2025-10-13	Night Republican always two figure majority season.	2026-08-14 18:11:01.310566+00
8d3d1f94-a654-49e9-9562-db98b1bba1b8	OTHER	0b7ee577-5db0-4984-bb45-6a0b6f221a99	fe76c92f-e973-45ca-9df1-1c6af7b8a105	\N	2023-09-03	\N	Green few you without every artist.	2026-08-14 18:11:01.310566+00
\.


--
-- Data for Name: conference_participations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.conference_participations (id, conference_id, researcher_id, publication_id, role, presentation_title, registered_at) FROM stdin;
2c7c3c7f-6290-413d-a638-d7a0a560fc3a	c8a66f8c-3093-4373-9967-7baf9b7ad418	3355eb65-55df-42bf-a3b6-7d8248931e82	\N	ATTENDEE	\N	2026-08-14 18:11:01.310566+00
5fff4e3d-9a02-4109-91ea-413d1e98147c	c8a66f8c-3093-4373-9967-7baf9b7ad418	b55e4655-6bd7-44c8-9f13-bd763db2fbeb	3506b4a7-97ac-48a4-a618-2713cc947e10	PRESENTER	Include plan step food drive nation	2026-08-14 18:11:01.310566+00
b3ff6521-d2a3-4bf9-bac9-80e7a080d965	c8a66f8c-3093-4373-9967-7baf9b7ad418	333ef9d3-4f76-487d-8e91-375c8588dbeb	bcb11c43-ed7f-4e1e-9e84-76eacd0a6e0d	PRESENTER	She unit effect which language however	2026-08-14 18:11:01.310566+00
8204fcdc-7df5-4fc3-a0cc-cb22cb633ed7	c8a66f8c-3093-4373-9967-7baf9b7ad418	cb3a20c1-c454-4452-9212-7bc4e800ee3e	\N	REVIEWER	\N	2026-08-14 18:11:01.310566+00
93e95047-fa19-4dd0-aa8c-02ddc76b421e	c8a66f8c-3093-4373-9967-7baf9b7ad418	06409b16-4619-4501-b1d5-b096c6e26201	\N	REVIEWER	\N	2026-08-14 18:11:01.310566+00
4515e1f7-91c7-45b2-b886-4436e4a163f1	c8a66f8c-3093-4373-9967-7baf9b7ad418	d34e909b-04b0-4e95-8b5f-712c1cb3aff3	\N	ORGANIZER	\N	2026-08-14 18:11:01.310566+00
0248dabe-1cb6-4b4e-a1b7-a20d52cd7ed7	c8a66f8c-3093-4373-9967-7baf9b7ad418	c28aab08-997a-444e-9b2a-a1a0f5a24732	14a17cd8-8c0d-4a8d-a025-8d2b951f56b5	PRESENTER	Work other military	2026-08-14 18:11:01.310566+00
16917116-302f-4b1a-a384-7dd1e1a28c1b	c8a66f8c-3093-4373-9967-7baf9b7ad418	6734f508-b66f-4566-977a-65bceaf98497	\N	ORGANIZER	\N	2026-08-14 18:11:01.310566+00
70e89b48-46ba-44ce-becb-9d36e636805b	aed0ca42-25c3-450b-bd7f-579654f885ee	518ab5a4-b1ae-45d5-b028-c0492d74c175	\N	ATTENDEE	\N	2026-08-14 18:11:01.310566+00
412bb043-2db7-4967-8fd8-bab69108bf92	aed0ca42-25c3-450b-bd7f-579654f885ee	54a8702d-c438-41ef-90db-8a16f87283b7	\N	REVIEWER	\N	2026-08-14 18:11:01.310566+00
da59206e-a727-4069-b632-f76e8be54633	aed0ca42-25c3-450b-bd7f-579654f885ee	c28aab08-997a-444e-9b2a-a1a0f5a24732	99c367d9-7330-430c-b9cf-b32fcf189201	PRESENTER	According worker Democrat fire sign	2026-08-14 18:11:01.310566+00
d33e6552-e9bd-4fb7-adba-063d0ebf22ac	aed0ca42-25c3-450b-bd7f-579654f885ee	5c451bd9-59fa-468f-bda4-882e46960305	\N	ATTENDEE	\N	2026-08-14 18:11:01.310566+00
3066ffc1-62c4-4346-b6ea-a4df342aebf4	aed0ca42-25c3-450b-bd7f-579654f885ee	333ef9d3-4f76-487d-8e91-375c8588dbeb	\N	ATTENDEE	\N	2026-08-14 18:11:01.310566+00
37fdff8d-fa0f-470e-a64d-d40826c14048	aed0ca42-25c3-450b-bd7f-579654f885ee	33b9cded-9912-4f7c-948d-bf43517357cb	\N	ORGANIZER	\N	2026-08-14 18:11:01.310566+00
efc36a21-de95-41f7-a414-d14dfc09b838	aed0ca42-25c3-450b-bd7f-579654f885ee	523b313b-2133-4286-a4ff-c2c1f49de6c6	\N	ATTENDEE	\N	2026-08-14 18:11:01.310566+00
0664a714-b088-4a69-bf6d-29556d75e3e0	aed0ca42-25c3-450b-bd7f-579654f885ee	06409b16-4619-4501-b1d5-b096c6e26201	a1c6b4e3-f162-49a1-97a6-137291fddbf7	PRESENTER	Try memory number occur behind	2026-08-14 18:11:01.310566+00
9e93a1c0-4dcb-402b-8a47-202057d0f823	aed0ca42-25c3-450b-bd7f-579654f885ee	6734f508-b66f-4566-977a-65bceaf98497	\N	ATTENDEE	\N	2026-08-14 18:11:01.310566+00
9fc81e92-6e27-48f0-9412-10f48a9d1187	fbef6df2-87d5-4c74-80d4-2943b2d90739	518ab5a4-b1ae-45d5-b028-c0492d74c175	\N	REVIEWER	\N	2026-08-14 18:11:01.310566+00
abedd6f3-95c5-4b14-af37-d989674abcec	fbef6df2-87d5-4c74-80d4-2943b2d90739	6734f508-b66f-4566-977a-65bceaf98497	\N	REVIEWER	\N	2026-08-14 18:11:01.310566+00
1e999908-45a2-4243-929e-9d174bb356d3	fbef6df2-87d5-4c74-80d4-2943b2d90739	54a8702d-c438-41ef-90db-8a16f87283b7	134f2502-5955-4f66-8bea-744adbb622b8	PRESENTER	Green catch happen old do specific begin	2026-08-14 18:11:01.310566+00
f8fd3347-6821-4d72-9db3-d0e3c3cc2bee	fbef6df2-87d5-4c74-80d4-2943b2d90739	3355eb65-55df-42bf-a3b6-7d8248931e82	6f7aa5ed-0a13-4a84-8493-7875e1e5c28d	PRESENTER	Notice design baby foot lot major	2026-08-14 18:11:01.310566+00
95623ff6-545a-4042-a4b5-99983ba570ce	fbef6df2-87d5-4c74-80d4-2943b2d90739	5c451bd9-59fa-468f-bda4-882e46960305	\N	REVIEWER	\N	2026-08-14 18:11:01.310566+00
ff9209fd-2399-4fe7-92b7-3d2cf21f488a	fbef6df2-87d5-4c74-80d4-2943b2d90739	8727c10d-53c2-41bd-9b5b-6475b544c1cd	\N	ORGANIZER	\N	2026-08-14 18:11:01.310566+00
d90f0296-c90e-4f7e-bc28-bbaf79f8b4db	fbef6df2-87d5-4c74-80d4-2943b2d90739	33b9cded-9912-4f7c-948d-bf43517357cb	\N	ORGANIZER	\N	2026-08-14 18:11:01.310566+00
2d0d3cf3-b925-4f87-b89e-a36c2de0c0b6	fbef6df2-87d5-4c74-80d4-2943b2d90739	c586faff-5d29-47ba-981a-d88e06187eec	00fc5533-b42d-4719-929f-5c7274281df1	PRESENTER	Standard believe politics also space high sister	2026-08-14 18:11:01.310566+00
b1b67924-4eee-4d3e-b3a8-37e69d376518	fbef6df2-87d5-4c74-80d4-2943b2d90739	b55e4655-6bd7-44c8-9f13-bd763db2fbeb	\N	ATTENDEE	\N	2026-08-14 18:11:01.310566+00
83a3df89-63cb-4d13-af27-eee142361004	fbef6df2-87d5-4c74-80d4-2943b2d90739	523b313b-2133-4286-a4ff-c2c1f49de6c6	ff038a64-ba2d-457b-8acf-db733fd9f68e	PRESENTER	Girl stage indicate test thank dinner	2026-08-14 18:11:01.310566+00
6f3f6365-3ecf-4fed-bd31-d88e3b73d3fd	e1d47d06-5926-40c1-8c47-9bd1a9ab80be	cb3a20c1-c454-4452-9212-7bc4e800ee3e	\N	REVIEWER	\N	2026-08-14 18:11:01.310566+00
ddcb5311-3e08-45fb-a565-405bdec4d064	e1d47d06-5926-40c1-8c47-9bd1a9ab80be	d34e909b-04b0-4e95-8b5f-712c1cb3aff3	\N	REVIEWER	\N	2026-08-14 18:11:01.310566+00
7e0d01ec-9f1e-4364-b9d5-d32918e4fbdc	e1d47d06-5926-40c1-8c47-9bd1a9ab80be	09127010-708d-491d-a823-9bfbfa417b90	0507ea92-778e-496b-829f-0b8fada69a1a	PRESENTER	Up plant place approach modern floor north force	2026-08-14 18:11:01.310566+00
dd12b55b-12e6-4ffd-8b11-502a588e16ec	e1d47d06-5926-40c1-8c47-9bd1a9ab80be	4c0075d2-ea71-40f6-a60a-c442557efd85	\N	ORGANIZER	\N	2026-08-14 18:11:01.310566+00
8b081e96-9f27-485d-bfc6-135a78381060	e1d47d06-5926-40c1-8c47-9bd1a9ab80be	6734f508-b66f-4566-977a-65bceaf98497	\N	REVIEWER	\N	2026-08-14 18:11:01.310566+00
85c563e7-975d-48ad-9a34-639410efe5f7	e1d47d06-5926-40c1-8c47-9bd1a9ab80be	06409b16-4619-4501-b1d5-b096c6e26201	\N	ORGANIZER	\N	2026-08-14 18:11:01.310566+00
edc681ac-48fa-4252-8df6-3aa27f31f4bb	e1d47d06-5926-40c1-8c47-9bd1a9ab80be	5c451bd9-59fa-468f-bda4-882e46960305	\N	ORGANIZER	\N	2026-08-14 18:11:01.310566+00
d5693745-bc2a-4587-a39d-456bd00d406c	e1d47d06-5926-40c1-8c47-9bd1a9ab80be	33b9cded-9912-4f7c-948d-bf43517357cb	dd4dafa6-23d4-44b8-88fc-54a480e0f779	PRESENTER	Check purpose young wife send	2026-08-14 18:11:01.310566+00
1144ee08-8c41-46c9-86a2-9c2993e9559b	e1d47d06-5926-40c1-8c47-9bd1a9ab80be	c28aab08-997a-444e-9b2a-a1a0f5a24732	\N	ATTENDEE	\N	2026-08-14 18:11:01.310566+00
804861e3-88c4-4b79-84ef-8571d6bf5827	805e8aeb-395c-4d24-9297-e9d9215c416f	c586faff-5d29-47ba-981a-d88e06187eec	bc6b8a77-87b1-4935-8aff-244cedf6adeb	PRESENTER	Measure develop face hour car bar number	2026-08-14 18:11:01.310566+00
512b0103-f6af-4ae2-b3b8-070b54016129	805e8aeb-395c-4d24-9297-e9d9215c416f	4c0075d2-ea71-40f6-a60a-c442557efd85	b52bae1b-4310-4b87-8c83-1e5fff7dc509	PRESENTER	Nature energy huge	2026-08-14 18:11:01.310566+00
ac026a95-c6dc-44b3-9387-5bffb3ee5340	805e8aeb-395c-4d24-9297-e9d9215c416f	518ab5a4-b1ae-45d5-b028-c0492d74c175	\N	ORGANIZER	\N	2026-08-14 18:11:01.310566+00
c4f9c5ad-2c92-413b-b9df-37e18282c842	805e8aeb-395c-4d24-9297-e9d9215c416f	523b313b-2133-4286-a4ff-c2c1f49de6c6	\N	ORGANIZER	\N	2026-08-14 18:11:01.310566+00
660660fe-7427-45ef-97c8-d6c970b1302c	805e8aeb-395c-4d24-9297-e9d9215c416f	6734f508-b66f-4566-977a-65bceaf98497	ff038a64-ba2d-457b-8acf-db733fd9f68e	PRESENTER	Similar candidate care nice maintain present	2026-08-14 18:11:01.310566+00
8adb5b27-71bf-4a66-929a-82ebe4d63879	805e8aeb-395c-4d24-9297-e9d9215c416f	333ef9d3-4f76-487d-8e91-375c8588dbeb	\N	REVIEWER	\N	2026-08-14 18:11:01.310566+00
757b4611-5e69-41d0-8215-44ca0b3b6a91	86e77718-be5a-49c6-88ba-892404f05f92	75724587-3aad-4f07-92b0-2ea0eb3a6aac	\N	REVIEWER	\N	2026-08-14 18:11:01.310566+00
ad5fb6b6-e99b-4cbd-a569-eb56314c5b77	86e77718-be5a-49c6-88ba-892404f05f92	a4ada868-9e1b-4f36-aba4-36de7818dcb8	c26ffc3f-1959-4153-8324-98713f7f80e0	PRESENTER	Night young modern drug entire	2026-08-14 18:11:01.310566+00
3d499ef9-7bfa-4dad-b84a-dfba030fad04	86e77718-be5a-49c6-88ba-892404f05f92	54a8702d-c438-41ef-90db-8a16f87283b7	\N	ORGANIZER	\N	2026-08-14 18:11:01.310566+00
65005a2f-350b-4cf0-90e5-a9922d397210	86e77718-be5a-49c6-88ba-892404f05f92	c586faff-5d29-47ba-981a-d88e06187eec	\N	ATTENDEE	\N	2026-08-14 18:11:01.310566+00
56c8ac8f-39e6-4156-945d-f0dbcf549429	86e77718-be5a-49c6-88ba-892404f05f92	333ef9d3-4f76-487d-8e91-375c8588dbeb	\N	ORGANIZER	\N	2026-08-14 18:11:01.310566+00
f95367ae-519f-47d1-b246-0b7c6591ea08	86e77718-be5a-49c6-88ba-892404f05f92	3355eb65-55df-42bf-a3b6-7d8248931e82	\N	REVIEWER	\N	2026-08-14 18:11:01.310566+00
934eefee-d698-4bc1-83ef-a5d7996e0bc6	86e77718-be5a-49c6-88ba-892404f05f92	cb3a20c1-c454-4452-9212-7bc4e800ee3e	\N	REVIEWER	\N	2026-08-14 18:11:01.310566+00
d9fe3d33-9734-4c01-a354-463bd5311707	86e77718-be5a-49c6-88ba-892404f05f92	09127010-708d-491d-a823-9bfbfa417b90	f001239a-86d6-42c5-9cef-e80a71bbaa2b	PRESENTER	Food under become public interest give	2026-08-14 18:11:01.310566+00
ea343890-4ab5-41f2-b789-6e4479c9e393	86e77718-be5a-49c6-88ba-892404f05f92	518ab5a4-b1ae-45d5-b028-c0492d74c175	\N	ATTENDEE	\N	2026-08-14 18:11:01.310566+00
b5a1f994-9222-43a8-9a47-2bf2dec59e3e	86e77718-be5a-49c6-88ba-892404f05f92	5c451bd9-59fa-468f-bda4-882e46960305	\N	ATTENDEE	\N	2026-08-14 18:11:01.310566+00
\.


--
-- Data for Name: conferences; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.conferences (id, name, location, website, start_date, end_date, created_at) FROM stdin;
c8a66f8c-3093-4373-9967-7baf9b7ad418	International Conference on Incubate Integrated Solutions	Cannonberg, New Zealand	https://davidson-rodriguez.net/	2026-08-04	2026-08-08	2026-08-14 18:11:01.310566+00
aed0ca42-25c3-450b-bd7f-579654f885ee	International Conference on Integrate End-To-End Roi	East Danielborough, Bolivia	http://burns.com/	2026-08-05	2026-08-09	2026-08-14 18:11:01.310566+00
fbef6df2-87d5-4c74-80d4-2943b2d90739	International Conference on Expedite Intuitive Synergies	Lake Travis, Tuvalu	http://brown.biz/	2025-09-18	2025-09-21	2026-08-14 18:11:01.310566+00
e1d47d06-5926-40c1-8c47-9bd1a9ab80be	International Conference on Generate Leading-Edge E-Business	Allisonland, Syrian Arab Republic	https://www.yu.com/	2027-01-30	2027-02-03	2026-08-14 18:11:01.310566+00
805e8aeb-395c-4d24-9297-e9d9215c416f	International Conference on Incubate Integrated Solutions	New Diane, Montenegro	http://garcia.info/	2026-10-16	2026-10-19	2026-08-14 18:11:01.310566+00
86e77718-be5a-49c6-88ba-892404f05f92	International Conference on Brand Sticky Communities	New Richard, Guadeloupe	http://orr-pierce.com/	2026-09-21	2026-09-22	2026-08-14 18:11:01.310566+00
\.


--
-- Data for Name: institutions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.institutions (id, name, country, address, website, institution_type, created_at, updated_at) FROM stdin;
fb075e07-3b72-496a-aad5-56344e096cb2	North Judithbury Research Center	Czech Republic	819 Johnson Course\nEast William, AK 74064	http://cole.com/	university	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
72e01afd-44ae-43a2-9176-9c9141919ac8	Lake Roberto University	Fiji	16155 Roman Stream Suite 816\nNew Kellystad, OK 25704	http://www.perez.com/	government_lab	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
e893353b-5e17-4b8e-8f8f-72f84e13be94	South Joshuastad University	Central African Republic	419 Amanda Gardens\nSouth Noah, SC 90699	http://perez.com/	research_institute	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
fe76c92f-e973-45ca-9df1-1c6af7b8a105	Adamsborough University	United States Minor Outlying Islands	USNV Lewis\nFPO AA 52357	https://www.taylor-mcgee.net/	university	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
542a3fc3-c5b9-4fc6-8b40-156c55077771	Juliechester Research Center	Ukraine	28710 Eric Estate Suite 916\nCarlsonmouth, NC 33454	http://www.dyer.com/	funding_organization	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
0b7ee577-5db0-4984-bb45-6a0b6f221a99	West Ryanmouth University	Afghanistan	USNV Stanton\nFPO AE 67043	http://romero.com/	funding_organization	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
\.


--
-- Data for Name: project_members; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.project_members (project_id, researcher_id, role, joined_at) FROM stdin;
a2ad2055-e403-43c5-8f54-503d3806c2f8	333ef9d3-4f76-487d-8e91-375c8588dbeb	Co-Investigator	2026-08-14 18:11:01.310566+00
a2ad2055-e403-43c5-8f54-503d3806c2f8	54a8702d-c438-41ef-90db-8a16f87283b7	Research Assistant	2026-08-14 18:11:01.310566+00
a2ad2055-e403-43c5-8f54-503d3806c2f8	33b9cded-9912-4f7c-948d-bf43517357cb	Contributor	2026-08-14 18:11:01.310566+00
a2ad2055-e403-43c5-8f54-503d3806c2f8	c586faff-5d29-47ba-981a-d88e06187eec	Co-Investigator	2026-08-14 18:11:01.310566+00
fbb6be02-ff59-4d57-b757-526c86ba0d5e	54a8702d-c438-41ef-90db-8a16f87283b7	Principal Investigator	2026-08-14 18:11:01.310566+00
fbb6be02-ff59-4d57-b757-526c86ba0d5e	333ef9d3-4f76-487d-8e91-375c8588dbeb	Principal Investigator	2026-08-14 18:11:01.310566+00
fbb6be02-ff59-4d57-b757-526c86ba0d5e	3355eb65-55df-42bf-a3b6-7d8248931e82	Principal Investigator	2026-08-14 18:11:01.310566+00
9498fea3-7d17-4abd-af01-f75e66f0d7ee	09127010-708d-491d-a823-9bfbfa417b90	Co-Investigator	2026-08-14 18:11:01.310566+00
9498fea3-7d17-4abd-af01-f75e66f0d7ee	c586faff-5d29-47ba-981a-d88e06187eec	Contributor	2026-08-14 18:11:01.310566+00
9498fea3-7d17-4abd-af01-f75e66f0d7ee	4c0075d2-ea71-40f6-a60a-c442557efd85	Principal Investigator	2026-08-14 18:11:01.310566+00
9498fea3-7d17-4abd-af01-f75e66f0d7ee	75724587-3aad-4f07-92b0-2ea0eb3a6aac	Co-Investigator	2026-08-14 18:11:01.310566+00
b9a0ec7a-10a0-40cf-ba7c-1204308a15e6	a4ada868-9e1b-4f36-aba4-36de7818dcb8	Contributor	2026-08-14 18:11:01.310566+00
b9a0ec7a-10a0-40cf-ba7c-1204308a15e6	523b313b-2133-4286-a4ff-c2c1f49de6c6	Co-Investigator	2026-08-14 18:11:01.310566+00
b9a0ec7a-10a0-40cf-ba7c-1204308a15e6	cb3a20c1-c454-4452-9212-7bc4e800ee3e	Co-Investigator	2026-08-14 18:11:01.310566+00
b9a0ec7a-10a0-40cf-ba7c-1204308a15e6	54a8702d-c438-41ef-90db-8a16f87283b7	Research Assistant	2026-08-14 18:11:01.310566+00
b9a0ec7a-10a0-40cf-ba7c-1204308a15e6	33b9cded-9912-4f7c-948d-bf43517357cb	Co-Investigator	2026-08-14 18:11:01.310566+00
b9a0ec7a-10a0-40cf-ba7c-1204308a15e6	b55e4655-6bd7-44c8-9f13-bd763db2fbeb	Principal Investigator	2026-08-14 18:11:01.310566+00
21dc6aea-6a05-4283-bb73-60d306288148	06409b16-4619-4501-b1d5-b096c6e26201	Contributor	2026-08-14 18:11:01.310566+00
21dc6aea-6a05-4283-bb73-60d306288148	d34e909b-04b0-4e95-8b5f-712c1cb3aff3	Co-Investigator	2026-08-14 18:11:01.310566+00
21dc6aea-6a05-4283-bb73-60d306288148	333ef9d3-4f76-487d-8e91-375c8588dbeb	Principal Investigator	2026-08-14 18:11:01.310566+00
20358546-5b74-4d23-bad4-ef38ec048f1c	09127010-708d-491d-a823-9bfbfa417b90	Co-Investigator	2026-08-14 18:11:01.310566+00
20358546-5b74-4d23-bad4-ef38ec048f1c	c28aab08-997a-444e-9b2a-a1a0f5a24732	Contributor	2026-08-14 18:11:01.310566+00
20358546-5b74-4d23-bad4-ef38ec048f1c	333ef9d3-4f76-487d-8e91-375c8588dbeb	Principal Investigator	2026-08-14 18:11:01.310566+00
6988648f-6986-4527-a818-e1ee41d26aba	6734f508-b66f-4566-977a-65bceaf98497	Research Assistant	2026-08-14 18:11:01.310566+00
6988648f-6986-4527-a818-e1ee41d26aba	d34e909b-04b0-4e95-8b5f-712c1cb3aff3	Research Assistant	2026-08-14 18:11:01.310566+00
6988648f-6986-4527-a818-e1ee41d26aba	c28aab08-997a-444e-9b2a-a1a0f5a24732	Co-Investigator	2026-08-14 18:11:01.310566+00
6988648f-6986-4527-a818-e1ee41d26aba	c586faff-5d29-47ba-981a-d88e06187eec	Research Assistant	2026-08-14 18:11:01.310566+00
70fa2799-e24d-4cde-ac1e-f3f9fc3b9eaa	cb3a20c1-c454-4452-9212-7bc4e800ee3e	Contributor	2026-08-14 18:11:01.310566+00
70fa2799-e24d-4cde-ac1e-f3f9fc3b9eaa	523b313b-2133-4286-a4ff-c2c1f49de6c6	Research Assistant	2026-08-14 18:11:01.310566+00
70fa2799-e24d-4cde-ac1e-f3f9fc3b9eaa	33b9cded-9912-4f7c-948d-bf43517357cb	Principal Investigator	2026-08-14 18:11:01.310566+00
70fa2799-e24d-4cde-ac1e-f3f9fc3b9eaa	518ab5a4-b1ae-45d5-b028-c0492d74c175	Principal Investigator	2026-08-14 18:11:01.310566+00
\.


--
-- Data for Name: projects; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.projects (id, title, description, funding_source, budget, status, start_date, end_date, lead_institution_id, lead_researcher_id, created_at, updated_at) FROM stdin;
a2ad2055-e403-43c5-8f54-503d3806c2f8	Synchronized web-enabled interface Research Initiative	Outside goal official defense prevent.\nGlass news boy everything. Southern suddenly window stand party.\nParticipant price really. Congress reflect finally. Go consider century price attorney scientist.\nSecond Democrat information game.	Internal Grant	94112.00	CANCELLED	2024-09-04	2026-09-21	72e01afd-44ae-43a2-9176-9c9141919ac8	6734f508-b66f-4566-977a-65bceaf98497	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
fbb6be02-ff59-4d57-b757-526c86ba0d5e	Synergistic optimizing matrix Research Initiative	Animal house out account feeling. Should share face build market. Compare herself region matter street south.\nTechnology amount affect TV television office. Identify policy face if whom commercial way.	EU Horizon	65080.00	PLANNED	2024-06-19	2026-09-23	fb075e07-3b72-496a-aad5-56344e096cb2	5c451bd9-59fa-468f-bda4-882e46960305	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
9498fea3-7d17-4abd-af01-f75e66f0d7ee	Exclusive context-sensitive portal Research Initiative	Concern significant management senior. Large under north play person ten physical character.\nKind field ever argue medical financial later. Hard expert popular within.\nOrder his oil west school American training occur. Focus little character artist billion.	National Science Foundation	1948803.00	PLANNED	2024-01-21	2025-06-22	fb075e07-3b72-496a-aad5-56344e096cb2	75724587-3aad-4f07-92b0-2ea0eb3a6aac	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
b9a0ec7a-10a0-40cf-ba7c-1204308a15e6	Robust coherent groupware Research Initiative	Professional true financial prevent product can remember be. Heavy social spend prove stock school rate.\nPosition interest gun guy. Week game she court. Choice fast small medical.	EU Horizon	634009.00	COMPLETED	2026-07-05	2027-08-08	542a3fc3-c5b9-4fc6-8b40-156c55077771	33b9cded-9912-4f7c-948d-bf43517357cb	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
21dc6aea-6a05-4283-bb73-60d306288148	Organic maximized throughput Research Initiative	Me industry class current painting their. Political them never.\nSurface expect several evening town challenge join. Stage this us increase how.\nHistory bank different five between. Social case expert stop receive catch. Large accept bad eight strong nature road.	DARPA	1258403.00	COMPLETED	2025-04-29	2026-07-01	fe76c92f-e973-45ca-9df1-1c6af7b8a105	c586faff-5d29-47ba-981a-d88e06187eec	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
20358546-5b74-4d23-bad4-ef38ec048f1c	Multi-lateral asymmetric moderator Research Initiative	Skill medical after them analysis hit health. Ground attack drop. Billion old series card good full poor store.\nPlace specific as simply leader fall analysis. Though firm financial huge spring. Education send course ground sit tend forward.	EU Horizon	247815.00	PLANNED	2023-11-15	2026-03-18	fe76c92f-e973-45ca-9df1-1c6af7b8a105	8727c10d-53c2-41bd-9b5b-6475b544c1cd	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
6988648f-6986-4527-a818-e1ee41d26aba	Implemented fresh-thinking benchmark Research Initiative	Produce fill owner international ready goal. Risk treatment past.\nPolice social arm provide image. Song quickly well central parent sit alone. Door population gun we.\nCheck last he know baby case happen fire.\nWhether ago control military trial. Energy employee land you.	Industry Partner	912143.00	COMPLETED	2024-02-27	2024-10-19	0b7ee577-5db0-4984-bb45-6a0b6f221a99	3355eb65-55df-42bf-a3b6-7d8248931e82	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
70fa2799-e24d-4cde-ac1e-f3f9fc3b9eaa	Total scalable conglomeration Research Initiative	Difference world society door management guess occur. Sound necessary partner beat finally yourself rest. Improve important offer by first avoid letter.\nCampaign stop necessary onto should can. Treat area buy check clearly follow remember. Way million exist bad cultural what.	National Science Foundation	894358.00	ON_HOLD	2025-09-28	2026-07-16	72e01afd-44ae-43a2-9176-9c9141919ac8	b55e4655-6bd7-44c8-9f13-bd763db2fbeb	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
\.


--
-- Data for Name: publication_authors; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.publication_authors (publication_id, researcher_id, author_order, is_corresponding) FROM stdin;
f001239a-86d6-42c5-9cef-e80a71bbaa2b	c586faff-5d29-47ba-981a-d88e06187eec	1	t
f001239a-86d6-42c5-9cef-e80a71bbaa2b	523b313b-2133-4286-a4ff-c2c1f49de6c6	2	f
a1c6b4e3-f162-49a1-97a6-137291fddbf7	a4ada868-9e1b-4f36-aba4-36de7818dcb8	1	t
a1c6b4e3-f162-49a1-97a6-137291fddbf7	523b313b-2133-4286-a4ff-c2c1f49de6c6	2	f
a1c6b4e3-f162-49a1-97a6-137291fddbf7	4c0075d2-ea71-40f6-a60a-c442557efd85	3	f
a1c6b4e3-f162-49a1-97a6-137291fddbf7	6734f508-b66f-4566-977a-65bceaf98497	4	f
a1c6b4e3-f162-49a1-97a6-137291fddbf7	09127010-708d-491d-a823-9bfbfa417b90	5	f
00fc5533-b42d-4719-929f-5c7274281df1	523b313b-2133-4286-a4ff-c2c1f49de6c6	1	t
00fc5533-b42d-4719-929f-5c7274281df1	c586faff-5d29-47ba-981a-d88e06187eec	2	f
00fc5533-b42d-4719-929f-5c7274281df1	5c451bd9-59fa-468f-bda4-882e46960305	3	f
c0d5d015-8261-405f-9c5b-02d890d1ccde	5c451bd9-59fa-468f-bda4-882e46960305	1	t
c0d5d015-8261-405f-9c5b-02d890d1ccde	cb3a20c1-c454-4452-9212-7bc4e800ee3e	2	f
c0d5d015-8261-405f-9c5b-02d890d1ccde	c586faff-5d29-47ba-981a-d88e06187eec	3	f
c0d5d015-8261-405f-9c5b-02d890d1ccde	4c0075d2-ea71-40f6-a60a-c442557efd85	4	f
6be5b5ef-f84d-4b49-aa84-ce493ba0c2cd	523b313b-2133-4286-a4ff-c2c1f49de6c6	1	t
3506b4a7-97ac-48a4-a618-2713cc947e10	523b313b-2133-4286-a4ff-c2c1f49de6c6	1	t
3506b4a7-97ac-48a4-a618-2713cc947e10	09127010-708d-491d-a823-9bfbfa417b90	2	f
3506b4a7-97ac-48a4-a618-2713cc947e10	54a8702d-c438-41ef-90db-8a16f87283b7	3	f
c26ffc3f-1959-4153-8324-98713f7f80e0	333ef9d3-4f76-487d-8e91-375c8588dbeb	1	t
c26ffc3f-1959-4153-8324-98713f7f80e0	a4ada868-9e1b-4f36-aba4-36de7818dcb8	2	f
14a17cd8-8c0d-4a8d-a025-8d2b951f56b5	6734f508-b66f-4566-977a-65bceaf98497	1	t
14a17cd8-8c0d-4a8d-a025-8d2b951f56b5	a4ada868-9e1b-4f36-aba4-36de7818dcb8	2	f
14a17cd8-8c0d-4a8d-a025-8d2b951f56b5	c28aab08-997a-444e-9b2a-a1a0f5a24732	3	f
14a17cd8-8c0d-4a8d-a025-8d2b951f56b5	c586faff-5d29-47ba-981a-d88e06187eec	4	f
4ca6b093-0b7f-4f21-bc26-dc643cb54721	54a8702d-c438-41ef-90db-8a16f87283b7	1	t
4ca6b093-0b7f-4f21-bc26-dc643cb54721	09127010-708d-491d-a823-9bfbfa417b90	2	f
ca41832d-5e7c-426d-a4be-b69a92c46b28	cb3a20c1-c454-4452-9212-7bc4e800ee3e	1	t
b52bae1b-4310-4b87-8c83-1e5fff7dc509	06409b16-4619-4501-b1d5-b096c6e26201	1	t
b52bae1b-4310-4b87-8c83-1e5fff7dc509	b55e4655-6bd7-44c8-9f13-bd763db2fbeb	2	f
b52bae1b-4310-4b87-8c83-1e5fff7dc509	54a8702d-c438-41ef-90db-8a16f87283b7	3	f
b52bae1b-4310-4b87-8c83-1e5fff7dc509	6734f508-b66f-4566-977a-65bceaf98497	4	f
77f2596a-cd30-4346-8056-1d5e8307dc61	523b313b-2133-4286-a4ff-c2c1f49de6c6	1	t
77f2596a-cd30-4346-8056-1d5e8307dc61	cb3a20c1-c454-4452-9212-7bc4e800ee3e	2	f
77f2596a-cd30-4346-8056-1d5e8307dc61	c586faff-5d29-47ba-981a-d88e06187eec	3	f
1aa6bf79-065c-4df0-a1b8-1108a163c186	c28aab08-997a-444e-9b2a-a1a0f5a24732	1	t
1aa6bf79-065c-4df0-a1b8-1108a163c186	4c0075d2-ea71-40f6-a60a-c442557efd85	2	f
1aa6bf79-065c-4df0-a1b8-1108a163c186	a4ada868-9e1b-4f36-aba4-36de7818dcb8	3	f
bcb11c43-ed7f-4e1e-9e84-76eacd0a6e0d	d34e909b-04b0-4e95-8b5f-712c1cb3aff3	1	t
bcb11c43-ed7f-4e1e-9e84-76eacd0a6e0d	8727c10d-53c2-41bd-9b5b-6475b544c1cd	2	f
bcb11c43-ed7f-4e1e-9e84-76eacd0a6e0d	5c451bd9-59fa-468f-bda4-882e46960305	3	f
bcb11c43-ed7f-4e1e-9e84-76eacd0a6e0d	c28aab08-997a-444e-9b2a-a1a0f5a24732	4	f
bcb11c43-ed7f-4e1e-9e84-76eacd0a6e0d	523b313b-2133-4286-a4ff-c2c1f49de6c6	5	f
bc6b8a77-87b1-4935-8aff-244cedf6adeb	a4ada868-9e1b-4f36-aba4-36de7818dcb8	1	t
0507ea92-778e-496b-829f-0b8fada69a1a	b55e4655-6bd7-44c8-9f13-bd763db2fbeb	1	t
0507ea92-778e-496b-829f-0b8fada69a1a	a4ada868-9e1b-4f36-aba4-36de7818dcb8	2	f
87df24d8-6606-4e0a-a5fd-1d3bb0ba57d2	33b9cded-9912-4f7c-948d-bf43517357cb	1	t
87df24d8-6606-4e0a-a5fd-1d3bb0ba57d2	5c451bd9-59fa-468f-bda4-882e46960305	2	f
87df24d8-6606-4e0a-a5fd-1d3bb0ba57d2	6734f508-b66f-4566-977a-65bceaf98497	3	f
87df24d8-6606-4e0a-a5fd-1d3bb0ba57d2	4c0075d2-ea71-40f6-a60a-c442557efd85	4	f
87df24d8-6606-4e0a-a5fd-1d3bb0ba57d2	06409b16-4619-4501-b1d5-b096c6e26201	5	f
99c367d9-7330-430c-b9cf-b32fcf189201	6734f508-b66f-4566-977a-65bceaf98497	1	t
b647712f-9cd9-41a4-955d-3949cc3120ea	54a8702d-c438-41ef-90db-8a16f87283b7	1	t
b647712f-9cd9-41a4-955d-3949cc3120ea	cb3a20c1-c454-4452-9212-7bc4e800ee3e	2	f
134f2502-5955-4f66-8bea-744adbb622b8	09127010-708d-491d-a823-9bfbfa417b90	1	t
134f2502-5955-4f66-8bea-744adbb622b8	3355eb65-55df-42bf-a3b6-7d8248931e82	2	f
134f2502-5955-4f66-8bea-744adbb622b8	6734f508-b66f-4566-977a-65bceaf98497	3	f
dd03b49e-9179-4b4f-9f4c-43ccc4f58480	3355eb65-55df-42bf-a3b6-7d8248931e82	1	t
dd03b49e-9179-4b4f-9f4c-43ccc4f58480	a4ada868-9e1b-4f36-aba4-36de7818dcb8	2	f
dd03b49e-9179-4b4f-9f4c-43ccc4f58480	518ab5a4-b1ae-45d5-b028-c0492d74c175	3	f
f13e9b82-ff81-4683-893c-7d27565709cb	523b313b-2133-4286-a4ff-c2c1f49de6c6	1	t
f13e9b82-ff81-4683-893c-7d27565709cb	6734f508-b66f-4566-977a-65bceaf98497	2	f
f13e9b82-ff81-4683-893c-7d27565709cb	b55e4655-6bd7-44c8-9f13-bd763db2fbeb	3	f
f13e9b82-ff81-4683-893c-7d27565709cb	c28aab08-997a-444e-9b2a-a1a0f5a24732	4	f
f13e9b82-ff81-4683-893c-7d27565709cb	518ab5a4-b1ae-45d5-b028-c0492d74c175	5	f
0d5dcfcb-ea96-4a41-81ae-74b9504667a3	3355eb65-55df-42bf-a3b6-7d8248931e82	1	t
0d5dcfcb-ea96-4a41-81ae-74b9504667a3	518ab5a4-b1ae-45d5-b028-c0492d74c175	2	f
20490192-eaef-4fcd-95ad-8d4e16d1775c	3355eb65-55df-42bf-a3b6-7d8248931e82	1	t
20490192-eaef-4fcd-95ad-8d4e16d1775c	d34e909b-04b0-4e95-8b5f-712c1cb3aff3	2	f
20490192-eaef-4fcd-95ad-8d4e16d1775c	8727c10d-53c2-41bd-9b5b-6475b544c1cd	3	f
20490192-eaef-4fcd-95ad-8d4e16d1775c	c586faff-5d29-47ba-981a-d88e06187eec	4	f
20490192-eaef-4fcd-95ad-8d4e16d1775c	06409b16-4619-4501-b1d5-b096c6e26201	5	f
ff038a64-ba2d-457b-8acf-db733fd9f68e	c28aab08-997a-444e-9b2a-a1a0f5a24732	1	t
ff038a64-ba2d-457b-8acf-db733fd9f68e	75724587-3aad-4f07-92b0-2ea0eb3a6aac	2	f
ff038a64-ba2d-457b-8acf-db733fd9f68e	06409b16-4619-4501-b1d5-b096c6e26201	3	f
c6a9f531-e79a-458d-8fd6-9d179c8acfcf	c586faff-5d29-47ba-981a-d88e06187eec	1	t
2c6330cb-76c8-4f7b-9147-13fdcfdfc038	3355eb65-55df-42bf-a3b6-7d8248931e82	1	t
2c6330cb-76c8-4f7b-9147-13fdcfdfc038	c586faff-5d29-47ba-981a-d88e06187eec	2	f
2c6330cb-76c8-4f7b-9147-13fdcfdfc038	8727c10d-53c2-41bd-9b5b-6475b544c1cd	3	f
2c6330cb-76c8-4f7b-9147-13fdcfdfc038	54a8702d-c438-41ef-90db-8a16f87283b7	4	f
dd4dafa6-23d4-44b8-88fc-54a480e0f779	c586faff-5d29-47ba-981a-d88e06187eec	1	t
dd4dafa6-23d4-44b8-88fc-54a480e0f779	09127010-708d-491d-a823-9bfbfa417b90	2	f
6f7aa5ed-0a13-4a84-8493-7875e1e5c28d	cb3a20c1-c454-4452-9212-7bc4e800ee3e	1	t
6f7aa5ed-0a13-4a84-8493-7875e1e5c28d	333ef9d3-4f76-487d-8e91-375c8588dbeb	2	f
6f7aa5ed-0a13-4a84-8493-7875e1e5c28d	4c0075d2-ea71-40f6-a60a-c442557efd85	3	f
6f7aa5ed-0a13-4a84-8493-7875e1e5c28d	54a8702d-c438-41ef-90db-8a16f87283b7	4	f
6f7aa5ed-0a13-4a84-8493-7875e1e5c28d	b55e4655-6bd7-44c8-9f13-bd763db2fbeb	5	f
40a99143-012b-4da7-8891-6121dfb22672	cb3a20c1-c454-4452-9212-7bc4e800ee3e	1	t
40a99143-012b-4da7-8891-6121dfb22672	06409b16-4619-4501-b1d5-b096c6e26201	2	f
40a99143-012b-4da7-8891-6121dfb22672	5c451bd9-59fa-468f-bda4-882e46960305	3	f
40a99143-012b-4da7-8891-6121dfb22672	c28aab08-997a-444e-9b2a-a1a0f5a24732	4	f
40a99143-012b-4da7-8891-6121dfb22672	33b9cded-9912-4f7c-948d-bf43517357cb	5	f
\.


--
-- Data for Name: publications; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.publications (id, title, abstract, publication_type, status, doi, journal_or_venue, volume, issue, pages, publication_date, file_path, project_id, created_at, updated_at) FROM stdin;
f001239a-86d6-42c5-9cef-e80a71bbaa2b	Ball we side enough decision	Peace air threat nation politics few. Source rate father authority art. Indeed less future century technology floor.\nCandidate have no five letter environment. Cell anything war ten industry. Spend value return couple.\nYou level these market bed hotel lead. Democrat good anything manager think.	PATENT	PUBLISHED	10.2638/af2307eb79	Multi-layered global open architecture Journal	5	2	260-436	2026-05-16	\N	20358546-5b74-4d23-bad4-ef38ec048f1c	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
a1c6b4e3-f162-49a1-97a6-137291fddbf7	Current meeting matter and case four	Lead paper middle foreign party class wrong. Order medical meeting majority none. Staff happy purpose woman on someone rise.\nOthers enter pretty. Officer return on color pick people subject challenge. All way body affect finish. Include data maybe particularly.\nRelationship million night your. Moment finish community treatment garden great sign. Particular court east newspaper different.	JOURNAL_PAPER	ARCHIVED	\N	Monitored zero administration website Journal	24	3	81-525	2023-03-16	\N	\N	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
00fc5533-b42d-4719-929f-5c7274281df1	Explain research get kind either	Dark Mrs usually receive case. Scientist dream anything toward difficult do beyond form. Beyond side accept nearly upon imagine various.\nPractice sense expert experience arrive shoulder present. Movement rich view tree company. Value already structure small.\nTheory across nothing blue work. Lawyer political modern threat care.	OTHER	PUBLISHED	10.9666/5a947a691c	Fully-configurable 24hour firmware Journal	1	3	54-369	2024-02-25	\N	fbb6be02-ff59-4d57-b757-526c86ba0d5e	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
c0d5d015-8261-405f-9c5b-02d890d1ccde	Send west few reveal activity president realize artist brother	If maybe time region. Real police wait happen determine.\nCheck security paper indeed near likely Mr. Seven quite other skin moment.\nBack nor article natural measure of. Clearly take kind quite. Major together knowledge argue car indeed nor next.\nHow staff second. Authority interest red must art thus worry line.\nConference career political role white hear. Large true help bag who themselves.	OTHER	PUBLISHED	10.5462/a762edce71	Optimized national implementation Journal	19	2	176-405	2025-11-28	\N	\N	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
6be5b5ef-f84d-4b49-aa84-ce493ba0c2cd	Leave choice country themselves she allow produce	Drive attack order. Our reflect any scientist I doctor describe. Cell year doctor trouble. Five our pull fly few century produce.\nFeel article we they treatment personal. New another general poor high modern.\nChance heavy senior list support feeling. South trip none whose. Morning home effort form bad last he.	BOOK	PUBLISHED	10.5114/f40be740b7	Triple-buffered demand-driven infrastructure Journal	4	1	217-442	2026-04-11	\N	20358546-5b74-4d23-bad4-ef38ec048f1c	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
3506b4a7-97ac-48a4-a618-2713cc947e10	Focus executive letter possible final growth third letter sort reveal	Have including none determine certainly. Network once result far cultural. Here street material pressure range.\nWhom politics make collection some college result. Contain threat wrong whatever model stuff avoid.\nInclude successful discuss.\nDespite lay art. Tree process administration mother in admit reveal movie.\nMaybe recently issue. Blood benefit chance court.	CONFERENCE_PAPER	PUBLISHED	10.5291/91ca385783	Centralized scalable access Journal	11	4	283-519	2025-06-05	\N	fbb6be02-ff59-4d57-b757-526c86ba0d5e	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
c26ffc3f-1959-4153-8324-98713f7f80e0	Matter its six not teach	Try discover top realize note even under. Tonight nor allow up fire.\nCertain star start up federal nor note support. Forward sense cause write right may window.\nJoin stuff future shoulder.\nWhy for plant situation late direction. Wait it quickly produce beat peace something. Bank child Republican plant. First blood accept final growth especially.\nCost large never impact. Bed never others.	JOURNAL_PAPER	ARCHIVED	\N	Up-sized responsive methodology Journal	10	1	190-599	2024-12-28	\N	6988648f-6986-4527-a818-e1ee41d26aba	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
14a17cd8-8c0d-4a8d-a025-8d2b951f56b5	Leader career according how success here	Friend spring teacher wind carry fly. Look concern huge five same. Whose site for exactly skill half usually.\nYoung conference should agree road wall decide something. Standard somebody important material.\nEducation child institution help last. Look husband media turn reality myself so growth.	CONFERENCE_PAPER	DRAFT	\N	Distributed grid-enabled algorithm Journal	24	1	184-408	\N	\N	\N	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
4ca6b093-0b7f-4f21-bc26-dc643cb54721	Bit indeed which break wait center find lay deal	Live just recent five feel special. Against gas body son. Might necessary former interview left.\nContinue policy it ahead pass culture or home. Day sell speak artist big. Cost for leader energy television month police.\nParticularly only girl suddenly pay sport. Try opportunity public finish draw. Consumer really memory industry. Offer institution main Mr.	OTHER	SUBMITTED	\N	Organic mobile concept Journal	36	4	80-422	\N	\N	\N	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
ca41832d-5e7c-426d-a4be-b69a92c46b28	Not somebody determine allow different	Sit not significant manager. Both box simple statement happen state among.\nDespite interesting save president easy themselves allow. Give stage keep yes simply. Decide scene ready technology particular.\nPattern size spend south. Go exactly much food region eye environment. World quickly believe while size try yeah.	CONFERENCE_PAPER	ARCHIVED	\N	Visionary background initiative Journal	2	2	171-511	2024-09-05	\N	\N	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
b52bae1b-4310-4b87-8c83-1e5fff7dc509	Reason theory lawyer maintain old than suggest	Play recently sure somebody huge why station. Environmental stock front official not magazine gas.\nBetween six least.\nKid a when dark. Think few themselves theory.\nEconomy head tough close how figure. Investment before believe degree back.\nMind knowledge account gas building. Really local director become south billion. Thing case similar send card year. Attention none particular clearly.	OTHER	ARCHIVED	\N	Right-sized uniform portal Journal	18	2	56-496	2023-10-04	\N	\N	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
77f2596a-cd30-4346-8056-1d5e8307dc61	Summer probably feeling military meeting	Position six soldier dream history. Matter order month within would. Car team nothing half raise several.\nOnto add democratic. We huge expert Republican.\nReduce bar Mr pattern everyone finally. Tv window choice force only shake power. Financial join well draw.\nUnder break partner area. Budget remain reduce clearly.	PATENT	SUBMITTED	\N	Profound high-level approach Journal	30	3	157-417	\N	\N	b9a0ec7a-10a0-40cf-ba7c-1204308a15e6	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
1aa6bf79-065c-4df0-a1b8-1108a163c186	Teacher cold church significant thus purpose boy scientist able	Animal hair turn condition whether.\nSort research pretty different eat trouble floor.\nHead maybe top conference source wonder west. Theory tend similar financial.\nLead hard factor six science drug happy. Young simply run national somebody character usually.\nMust player really act friend.\nBillion morning draw man art. Republican behavior TV today. Including time learn security oil measure PM.	PATENT	PUBLISHED	10.2137/4e5a2c4483	Customer-focused composite knowledge user Journal	18	3	261-505	2024-06-24	\N	\N	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
bcb11c43-ed7f-4e1e-9e84-76eacd0a6e0d	Building group show later leg system bed space	American structure foreign before eat green message quality. Star community weight take new.\nBehind big soldier building article. Candidate statement head piece popular. Only true avoid young cup position speak begin.\nAmount leave collection off. Many him interview government traditional every. Third alone people early far include nearly.	TECHNICAL_REPORT	PUBLISHED	10.1452/502c8382ac	Pre-emptive grid-enabled open system Journal	8	3	92-598	2024-08-16	\N	\N	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
bc6b8a77-87b1-4935-8aff-244cedf6adeb	Establish ago others ahead specific exactly speak line	Yourself wind beyond prevent entire staff true argue. Offer work home very yard. Compare or south recently.\nRegion goal nothing. None could write think. My compare also argue own after long. Truth cut candidate response try such.\nAgainst only true similar. Team whether health walk how big few. Wish run join police.	BOOK	DRAFT	\N	Digitized full-range synergy Journal	39	4	177-461	\N	\N	fbb6be02-ff59-4d57-b757-526c86ba0d5e	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
0507ea92-778e-496b-829f-0b8fada69a1a	Draw word collection those become	Activity decide really go skin result answer. Run why this manage her national. Stock small official serve.\nLater son almost after. Weight avoid color heart rule.\nFull world throw relate. Wall close threat church big day. Important never understand music produce.\nBenefit hotel near make approach. Into far product.	PATENT	ARCHIVED	\N	Quality-focused incremental system engine Journal	13	3	23-524	2024-12-22	\N	b9a0ec7a-10a0-40cf-ba7c-1204308a15e6	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
87df24d8-6606-4e0a-a5fd-1d3bb0ba57d2	Article hit mission whole reach view of dog federal house	Number might number work challenge we last.\nSpeak call interest write itself. Challenge organization floor road southern beautiful news need.\nLeader them skill performance mission information increase. Note old who beyond.\nSingle size test they there enough pressure. Participant also every century participant really although.	BOOK	PUBLISHED	10.6409/f7849d4ad1	Operative real-time project Journal	40	3	64-454	2022-12-22	\N	6988648f-6986-4527-a818-e1ee41d26aba	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
99c367d9-7330-430c-b9cf-b32fcf189201	Deep station scientist service test start middle city find	Career surface these ahead cover strategy. Economic lead truth relate. Happy less however type race.\nMajor land whether listen necessary general. See read expect hit clear.\nTax positive question especially important. Ten whose radio. Treatment positive over across education source figure.\nTime surface learn design few minute. However bill memory production successful hear positive participant.	BOOK	PUBLISHED	10.5844/8063309d72	Virtual disintermediate approach Journal	36	2	99-516	2025-11-02	\N	\N	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
b647712f-9cd9-41a4-955d-3949cc3120ea	Identify floor cause agent market fast trade identify say on	Gas require rather point little. Medical suddenly subject theory Congress best. Scientist rise next tree.\nDevelop development the inside. He one less brother approach plant. Want author threat matter test high fear approach.\nYeah garden would throughout. Century television Congress ball forward would finish.\nLater decide similar. Share majority shake because pass plant idea.	PATENT	PUBLISHED	10.3851/211c8c744f	Programmable radical moderator Journal	40	3	208-581	2023-12-20	\N	\N	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
134f2502-5955-4f66-8bea-744adbb622b8	Garden top grow could way truth	Direction road capital. Operation college hand. Heart policy side.\nOrder answer blue. Answer break know. Natural listen check receive. Act inside big minute performance red industry together.\nBrother box blood cup current enjoy mission cut. Far always many debate value former. Actually become book.	BOOK	SUBMITTED	\N	Devolved stable project Journal	28	3	239-527	\N	\N	b9a0ec7a-10a0-40cf-ba7c-1204308a15e6	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
dd03b49e-9179-4b4f-9f4c-43ccc4f58480	Forget thus western environmental run head	Box hundred lead structure. Son power someone both receive around wall. Billion treat lot notice.\nParticularly single particularly television. Low maintain thought key. Energy fire relate question.\nDifference what their mind read peace item. Loss professional political chance step. Approach poor church support system thank avoid man.	TECHNICAL_REPORT	PUBLISHED	10.3780/4ebe9cd94a	Ameliorated bi-directional initiative Journal	6	3	264-472	2024-04-07	\N	b9a0ec7a-10a0-40cf-ba7c-1204308a15e6	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
f13e9b82-ff81-4683-893c-7d27565709cb	Near stay social white point three none pressure lay future	Such forward should outside respond.\nBox service develop game stop who factor. Hear blood to manage state score important. Particularly could us hotel lead.\nBlue increase unit study open sign. Leader operation mean white above save network.\nLot meet TV concern official room campaign hold. Paper focus thing industry participant realize eat huge. Wife laugh card include record security.	OTHER	PUBLISHED	10.4262/00e97801af	Sharable fresh-thinking strategy Journal	10	1	24-426	2023-01-29	\N	\N	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
0d5dcfcb-ea96-4a41-81ae-74b9504667a3	No old wall report purpose throw move there	Mission agent certainly. Customer seek claim expert. Chair artist six daughter must.\nBill test science ten score night down. Realize another high indicate small. Whole approach season data than team.\nTreatment relate positive sense national. Cultural right cover large work avoid while same. Help investment news candidate.	TECHNICAL_REPORT	ARCHIVED	\N	Versatile regional moderator Journal	5	4	213-595	2024-07-07	\N	6988648f-6986-4527-a818-e1ee41d26aba	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
20490192-eaef-4fcd-95ad-8d4e16d1775c	Statement wonder across protect knowledge toward party perform where radio	Trouble war history music executive treat. Method meet main fast prepare fly. Way cold what Mrs.\nAssume prove similar ten interest billion Mrs reflect.\nSection child learn forward. Available concern edge audience. Treat imagine later identify first.\nMovement political peace series. Animal summer group me face rate paper example. High state air choose detail section.	PATENT	PUBLISHED	10.3417/018578b93e	Open-source secondary migration Journal	1	1	218-413	2023-03-10	\N	70fa2799-e24d-4cde-ac1e-f3f9fc3b9eaa	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
ff038a64-ba2d-457b-8acf-db733fd9f68e	Determine strong create consider son system	Popular available public economy culture oil week. Campaign pretty beyond people too fish. Foreign process really charge note space when.\nFinish size Republican. Everybody growth quickly former lose knowledge.\nNecessary compare parent success teach cause Mrs. Safe phone road throughout support.	JOURNAL_PAPER	PUBLISHED	10.2988/d8aac90f52	Front-line reciprocal software Journal	30	2	238-572	2023-04-13	\N	\N	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
c6a9f531-e79a-458d-8fd6-9d179c8acfcf	Cell city not not the certainly rule voice American seven	Enough doctor protect military. Hold truth thing always possible billion.\nStrong enjoy name community president. Onto together back edge win development. Good test main lot page maybe.\nClose baby poor deep cost gun. Produce increase form box.\nDecision claim street against amount of claim. Mention three chair coach two might if wide. These road start.	TECHNICAL_REPORT	PUBLISHED	10.8251/bcffce44a6	Right-sized optimizing architecture Journal	40	4	281-529	2023-07-15	\N	\N	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
2c6330cb-76c8-4f7b-9147-13fdcfdfc038	Car admit mission training range step painting concern	Although six me brother lot candidate owner still. Miss have analysis morning director sort. Go source traditional student office international. Local discussion teacher exist theory.\nCountry remember smile official brother. Heart day sound. Gun choice prepare effect talk interest.\nEvery quite sense including six lot have never. Write officer similar huge catch. Security land record class.	OTHER	ARCHIVED	\N	Right-sized intermediate array Journal	29	3	127-442	2022-11-15	\N	\N	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
dd4dafa6-23d4-44b8-88fc-54a480e0f779	He participant right us husband prevent expert	Watch star policy keep. Sure us million crime six. Middle discuss college already dream a church. Sister good house only military.\nNear risk next on. White everybody paper create upon offer.\nImagine blood authority family. Sort what then spend.\nReason whom none show serious. Race to television loss election him small. Quality discover firm western might.\nEat behavior purpose start away.	TECHNICAL_REPORT	PUBLISHED	10.4919/448c91b96a	Secured heuristic collaboration Journal	18	4	40-447	2025-09-25	\N	20358546-5b74-4d23-bad4-ef38ec048f1c	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
6f7aa5ed-0a13-4a84-8493-7875e1e5c28d	Turn put professional pass share must	He firm together thing off ever consumer.\nHuge seek campaign moment institution. Allow girl team simply lead build million. Ready activity decision ok foot party.\nNature down likely party. Contain interest industry sell half hundred.\nNumber without rather sport. Sound new task cultural son. List act instead care.	BOOK	ARCHIVED	\N	Vision-oriented executive help-desk Journal	6	2	78-419	2023-12-01	\N	9498fea3-7d17-4abd-af01-f75e66f0d7ee	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
40a99143-012b-4da7-8891-6121dfb22672	Maintain say threat high expert place certain cold space front	Occur support author class direction first fact environment. Even know television guy only whole. Cold take by doctor edge season. Decision however believe view.\nApproach side model you billion peace base. Finally easy exist phone capital stuff. Along ground trip.\nWindow music evening know wide recently computer. Lead see theory itself policy move training loss. Source kind hand employee field.	OTHER	SUBMITTED	\N	Polarized exuding access Journal	27	4	170-578	\N	\N	a2ad2055-e403-43c5-8f54-503d3806c2f8	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
\.


--
-- Data for Name: researcher_tags; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.researcher_tags (researcher_id, tag_id) FROM stdin;
a4ada868-9e1b-4f36-aba4-36de7818dcb8	cab93e31-a514-4338-af7f-67d2a7fe346d
a4ada868-9e1b-4f36-aba4-36de7818dcb8	0572ca64-8244-4bf9-84d8-f15098359dd1
a4ada868-9e1b-4f36-aba4-36de7818dcb8	8c9a442a-f877-4ab9-83bc-63e1e5fc3c05
a4ada868-9e1b-4f36-aba4-36de7818dcb8	de675499-001c-415d-ada0-8758207acd5c
d34e909b-04b0-4e95-8b5f-712c1cb3aff3	3fa39aff-99ed-485a-9035-e2f267a1df67
d34e909b-04b0-4e95-8b5f-712c1cb3aff3	c2643739-ff93-4e18-a7d4-839241ebf91d
d34e909b-04b0-4e95-8b5f-712c1cb3aff3	141c53dc-fcfc-40c9-a565-7ca93b21238d
d34e909b-04b0-4e95-8b5f-712c1cb3aff3	e5f2830a-a04a-4e63-b130-c7a0fbab9bc9
c28aab08-997a-444e-9b2a-a1a0f5a24732	438b9ac3-9fce-49d9-9f24-d2b48c9a6567
c28aab08-997a-444e-9b2a-a1a0f5a24732	ae683b0d-2085-4fae-be2b-5eedf05d23f1
c28aab08-997a-444e-9b2a-a1a0f5a24732	122396e4-c9b5-45e2-981c-af1363fe81ab
c28aab08-997a-444e-9b2a-a1a0f5a24732	8fda1271-2dbe-4f21-bfb8-c96ec304ddc5
3355eb65-55df-42bf-a3b6-7d8248931e82	28abb28d-e9e1-4c1e-a98e-66097f5e1421
3355eb65-55df-42bf-a3b6-7d8248931e82	cab93e31-a514-4338-af7f-67d2a7fe346d
3355eb65-55df-42bf-a3b6-7d8248931e82	122396e4-c9b5-45e2-981c-af1363fe81ab
3355eb65-55df-42bf-a3b6-7d8248931e82	8fda1271-2dbe-4f21-bfb8-c96ec304ddc5
33b9cded-9912-4f7c-948d-bf43517357cb	ae683b0d-2085-4fae-be2b-5eedf05d23f1
33b9cded-9912-4f7c-948d-bf43517357cb	0572ca64-8244-4bf9-84d8-f15098359dd1
33b9cded-9912-4f7c-948d-bf43517357cb	de675499-001c-415d-ada0-8758207acd5c
33b9cded-9912-4f7c-948d-bf43517357cb	6e397eb7-5486-40d5-b2f3-d84bed970b70
09127010-708d-491d-a823-9bfbfa417b90	438b9ac3-9fce-49d9-9f24-d2b48c9a6567
09127010-708d-491d-a823-9bfbfa417b90	bd596e6c-7260-455e-8e7a-510d6b73c041
09127010-708d-491d-a823-9bfbfa417b90	79b05aba-331f-409d-8524-beba605d003b
09127010-708d-491d-a823-9bfbfa417b90	8b95dcd6-40ee-440d-b84c-5a8a82eddce0
b55e4655-6bd7-44c8-9f13-bd763db2fbeb	cab93e31-a514-4338-af7f-67d2a7fe346d
b55e4655-6bd7-44c8-9f13-bd763db2fbeb	5ed2ef63-d818-43f7-8eb3-f64974ad3049
b55e4655-6bd7-44c8-9f13-bd763db2fbeb	e5f2830a-a04a-4e63-b130-c7a0fbab9bc9
b55e4655-6bd7-44c8-9f13-bd763db2fbeb	371585b4-03e1-42e5-af74-8475deba4af7
5c451bd9-59fa-468f-bda4-882e46960305	5ed2ef63-d818-43f7-8eb3-f64974ad3049
5c451bd9-59fa-468f-bda4-882e46960305	0572ca64-8244-4bf9-84d8-f15098359dd1
5c451bd9-59fa-468f-bda4-882e46960305	79b05aba-331f-409d-8524-beba605d003b
5c451bd9-59fa-468f-bda4-882e46960305	8fda1271-2dbe-4f21-bfb8-c96ec304ddc5
cb3a20c1-c454-4452-9212-7bc4e800ee3e	28abb28d-e9e1-4c1e-a98e-66097f5e1421
cb3a20c1-c454-4452-9212-7bc4e800ee3e	39872157-4711-49f5-9328-ec64657a76e3
cb3a20c1-c454-4452-9212-7bc4e800ee3e	371585b4-03e1-42e5-af74-8475deba4af7
cb3a20c1-c454-4452-9212-7bc4e800ee3e	e5f2830a-a04a-4e63-b130-c7a0fbab9bc9
518ab5a4-b1ae-45d5-b028-c0492d74c175	3fa39aff-99ed-485a-9035-e2f267a1df67
518ab5a4-b1ae-45d5-b028-c0492d74c175	39872157-4711-49f5-9328-ec64657a76e3
518ab5a4-b1ae-45d5-b028-c0492d74c175	8b95dcd6-40ee-440d-b84c-5a8a82eddce0
518ab5a4-b1ae-45d5-b028-c0492d74c175	8fda1271-2dbe-4f21-bfb8-c96ec304ddc5
06409b16-4619-4501-b1d5-b096c6e26201	0572ca64-8244-4bf9-84d8-f15098359dd1
06409b16-4619-4501-b1d5-b096c6e26201	ae683b0d-2085-4fae-be2b-5eedf05d23f1
06409b16-4619-4501-b1d5-b096c6e26201	e5f2830a-a04a-4e63-b130-c7a0fbab9bc9
06409b16-4619-4501-b1d5-b096c6e26201	8b95dcd6-40ee-440d-b84c-5a8a82eddce0
8727c10d-53c2-41bd-9b5b-6475b544c1cd	3fa39aff-99ed-485a-9035-e2f267a1df67
8727c10d-53c2-41bd-9b5b-6475b544c1cd	28abb28d-e9e1-4c1e-a98e-66097f5e1421
8727c10d-53c2-41bd-9b5b-6475b544c1cd	8c9a442a-f877-4ab9-83bc-63e1e5fc3c05
8727c10d-53c2-41bd-9b5b-6475b544c1cd	6e397eb7-5486-40d5-b2f3-d84bed970b70
523b313b-2133-4286-a4ff-c2c1f49de6c6	438b9ac3-9fce-49d9-9f24-d2b48c9a6567
523b313b-2133-4286-a4ff-c2c1f49de6c6	ae683b0d-2085-4fae-be2b-5eedf05d23f1
523b313b-2133-4286-a4ff-c2c1f49de6c6	6e397eb7-5486-40d5-b2f3-d84bed970b70
523b313b-2133-4286-a4ff-c2c1f49de6c6	8fda1271-2dbe-4f21-bfb8-c96ec304ddc5
c586faff-5d29-47ba-981a-d88e06187eec	bd596e6c-7260-455e-8e7a-510d6b73c041
c586faff-5d29-47ba-981a-d88e06187eec	cab93e31-a514-4338-af7f-67d2a7fe346d
c586faff-5d29-47ba-981a-d88e06187eec	122396e4-c9b5-45e2-981c-af1363fe81ab
c586faff-5d29-47ba-981a-d88e06187eec	6e397eb7-5486-40d5-b2f3-d84bed970b70
54a8702d-c438-41ef-90db-8a16f87283b7	bd596e6c-7260-455e-8e7a-510d6b73c041
54a8702d-c438-41ef-90db-8a16f87283b7	cab93e31-a514-4338-af7f-67d2a7fe346d
54a8702d-c438-41ef-90db-8a16f87283b7	8c9a442a-f877-4ab9-83bc-63e1e5fc3c05
54a8702d-c438-41ef-90db-8a16f87283b7	141c53dc-fcfc-40c9-a565-7ca93b21238d
4c0075d2-ea71-40f6-a60a-c442557efd85	c2643739-ff93-4e18-a7d4-839241ebf91d
4c0075d2-ea71-40f6-a60a-c442557efd85	5ed2ef63-d818-43f7-8eb3-f64974ad3049
4c0075d2-ea71-40f6-a60a-c442557efd85	141c53dc-fcfc-40c9-a565-7ca93b21238d
4c0075d2-ea71-40f6-a60a-c442557efd85	de675499-001c-415d-ada0-8758207acd5c
75724587-3aad-4f07-92b0-2ea0eb3a6aac	cab93e31-a514-4338-af7f-67d2a7fe346d
75724587-3aad-4f07-92b0-2ea0eb3a6aac	bd596e6c-7260-455e-8e7a-510d6b73c041
75724587-3aad-4f07-92b0-2ea0eb3a6aac	e5f2830a-a04a-4e63-b130-c7a0fbab9bc9
75724587-3aad-4f07-92b0-2ea0eb3a6aac	371585b4-03e1-42e5-af74-8475deba4af7
333ef9d3-4f76-487d-8e91-375c8588dbeb	cab93e31-a514-4338-af7f-67d2a7fe346d
333ef9d3-4f76-487d-8e91-375c8588dbeb	5ed2ef63-d818-43f7-8eb3-f64974ad3049
333ef9d3-4f76-487d-8e91-375c8588dbeb	6e397eb7-5486-40d5-b2f3-d84bed970b70
333ef9d3-4f76-487d-8e91-375c8588dbeb	8fda1271-2dbe-4f21-bfb8-c96ec304ddc5
6734f508-b66f-4566-977a-65bceaf98497	ae683b0d-2085-4fae-be2b-5eedf05d23f1
6734f508-b66f-4566-977a-65bceaf98497	5ed2ef63-d818-43f7-8eb3-f64974ad3049
6734f508-b66f-4566-977a-65bceaf98497	de675499-001c-415d-ada0-8758207acd5c
6734f508-b66f-4566-977a-65bceaf98497	122396e4-c9b5-45e2-981c-af1363fe81ab
\.


--
-- Data for Name: researchers; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.researchers (id, user_id, institution_id, full_name, department, academic_title, orcid_id, bio, created_at, updated_at) FROM stdin;
a4ada868-9e1b-4f36-aba4-36de7818dcb8	e31e92f6-b5cd-4f32-89b0-f7e0f60fce6c	fe76c92f-e973-45ca-9df1-1c6af7b8a105	Sherry Decker	Computer Science	Professor	0000-0001-4582-4811	Around there water beat magazine. Within mouth call process.\nEnter their institution deep. Sense ready require human public health tonight. Building different full open discover detail audience.	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
d34e909b-04b0-4e95-8b5f-712c1cb3aff3	98b249da-4683-49ae-9816-219d5e88bc28	0b7ee577-5db0-4984-bb45-6a0b6f221a99	Clifford Ford	Engineering	Research Scientist	0000-0002-4611-8359	Space task better present music address. Unit support coach magazine.\nTotal clearly able hospital unit size. Institution whatever yet new responsibility.	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
c28aab08-997a-444e-9b2a-a1a0f5a24732	8c111f53-82bc-4a04-9266-43038fa783a1	0b7ee577-5db0-4984-bb45-6a0b6f221a99	Barry Hensley	Chemistry	Postdoctoral Researcher	0000-0002-3547-4527	Walk now often always. Information on mission various. Prove fire enter capital population.	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
3355eb65-55df-42bf-a3b6-7d8248931e82	89502bcf-b017-4a0e-973b-6b2de3645509	fb075e07-3b72-496a-aad5-56344e096cb2	Natalie Moore	Biology	Postdoctoral Researcher	0000-0003-5333-1711	Decision garden reach table measure economy traditional anything. Stop analysis four capital woman claim.	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
33b9cded-9912-4f7c-948d-bf43517357cb	8be42812-a925-40d3-a126-67dd60185abf	fb075e07-3b72-496a-aad5-56344e096cb2	Nicole Frost	Mathematics	Postdoctoral Researcher	0000-0003-6925-4150	Wish specific thing agent. Site in prove same easy city.\nThe teach develop staff least figure. Development process huge everything attorney.	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
09127010-708d-491d-a823-9bfbfa417b90	690410a3-7272-493b-a4e6-5453d9be8f66	fb075e07-3b72-496a-aad5-56344e096cb2	Cheryl Williams	Physics	Professor	0000-0002-5554-8428	Mind southern rather. Hair attorney professional form finish. Rest feel finally impact.\nNever court professor here security. Past feeling nature a. Decision size parent focus kid.	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
b55e4655-6bd7-44c8-9f13-bd763db2fbeb	8a2d6529-7abd-4364-9540-11912547f543	72e01afd-44ae-43a2-9176-9c9141919ac8	Stephen Johnston	Engineering	Postdoctoral Researcher	0000-0003-2169-3803	Hundred challenge reach throughout team those sing. Compare when military anyone eat. Lead soon property write.	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
5c451bd9-59fa-468f-bda4-882e46960305	4eff9dc0-b6e7-492d-bee1-3186ca4a3f4e	fe76c92f-e973-45ca-9df1-1c6af7b8a105	Daniel Fisher	Biology	Research Scientist	0000-0001-6313-1916	Task she herself. Wall fear hope. Mrs same son today major event. Ahead from quickly identify close level camera.	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
cb3a20c1-c454-4452-9212-7bc4e800ee3e	11b7b056-32a9-4824-98c1-1d5b0e8183fa	e893353b-5e17-4b8e-8f8f-72f84e13be94	Andre Wright	Computer Science	Associate Professor	0000-0003-6155-4483	Charge call prove nor design record short cold.\nSing clearly find official. Office traditional heart walk cup. Real physical big significant sure outside building worker. Girl into have.	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
518ab5a4-b1ae-45d5-b028-c0492d74c175	66382120-b3bb-4575-bddd-077dfbf62091	e893353b-5e17-4b8e-8f8f-72f84e13be94	Jamie Johnson	Physics	Associate Professor	0000-0003-9830-5304	Maintain great election evidence. Red everybody act way beat result major serve. Position make society behavior develop reality fill.	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
06409b16-4619-4501-b1d5-b096c6e26201	41cc97db-e8da-40fc-b33f-11e77be6680f	e893353b-5e17-4b8e-8f8f-72f84e13be94	Tony Little	Physics	Associate Professor	0000-0003-9085-2489	Their off light key. Whole education technology box. Husband available picture approach.\nWe be easy newspaper indicate other peace. Herself training father open investment notice art.	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
8727c10d-53c2-41bd-9b5b-6475b544c1cd	7428238c-3b9f-4cb0-b60a-347c90c4763c	0b7ee577-5db0-4984-bb45-6a0b6f221a99	David Baker	Chemistry	Research Scientist	0000-0001-7304-7252	Product value interesting name positive training step author. Society organization station TV. Buy read record wall matter management. Our threat same page.\nDirector purpose team onto.	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
523b313b-2133-4286-a4ff-c2c1f49de6c6	cc3f4dc2-76d5-4ce7-bda2-f35f46bdde04	542a3fc3-c5b9-4fc6-8b40-156c55077771	Tracy Harrison	Computer Science	Professor	0000-0003-9797-5371	Fly bit claim in many production. Spend nearly lawyer fire follow wife. Ten stay ability thank left approach.	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
c586faff-5d29-47ba-981a-d88e06187eec	c772dbcb-9e87-42cf-867e-80b088df835a	72e01afd-44ae-43a2-9176-9c9141919ac8	Dr. Jordan Hill PhD	Chemistry	Professor	0000-0003-5315-9201	Lead certain course out second. Tell everybody so increase. Environment able rise study oil process tend.	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
54a8702d-c438-41ef-90db-8a16f87283b7	5b33d6ea-5ab8-4dda-87bf-524ffb156597	0b7ee577-5db0-4984-bb45-6a0b6f221a99	Alexis Thomas	Mathematics	Research Scientist	0000-0001-3504-7126	Light wide full realize. System system teacher here.\nResponsibility service their along attention piece TV young. Its better plant their. Coach federal ahead food argue grow.	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
4c0075d2-ea71-40f6-a60a-c442557efd85	3c348e00-1b8b-421a-a37e-4b0ac3eb5e91	542a3fc3-c5b9-4fc6-8b40-156c55077771	Victor Vaughn	Biology	PhD Candidate	0000-0001-2832-6947	Current his low down occur. Fast recognize against stop how account ten. Treat seat strategy.\nParent good PM per question. Pick tough position final.	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
75724587-3aad-4f07-92b0-2ea0eb3a6aac	7ba8716a-9273-4b37-be16-704d70f54b58	542a3fc3-c5b9-4fc6-8b40-156c55077771	Brenda Levy	Computer Science	Professor	0000-0003-8962-2133	Hand so add Mr lawyer pull public. Herself police he push likely people wall foreign. Determine as statement travel few impact cause watch.	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
333ef9d3-4f76-487d-8e91-375c8588dbeb	c5903f6d-079a-4f17-b8d5-7fbbb07c5508	542a3fc3-c5b9-4fc6-8b40-156c55077771	David Cox	Physics	Postdoctoral Researcher	0000-0003-7932-4470	Top population art every why we station. Production politics others again. During call north attention share debate.\nForget challenge too able teach. Would music sometimes body.\nAddress so draw food.	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
6734f508-b66f-4566-977a-65bceaf98497	5acecdbb-611f-4272-afe1-98665f118aba	0b7ee577-5db0-4984-bb45-6a0b6f221a99	Jessica Rodriguez	Engineering	Postdoctoral Researcher	0000-0002-9479-8397	Tonight focus chance call. Plan nature foot yes most law painting between. Table prepare shoulder result.\nLater direction fund law indeed believe. Fine effort well rather listen before.	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
b01d8db2-2788-4243-881b-ab6f489d5fcd	3b277ce0-d701-462f-bfc0-67624b0c5087	fb075e07-3b72-496a-aad5-56344e096cb2	Researcher Demo	Computer Science	Researcher	\N	\N	2026-08-14 18:11:40.773146+00	2026-08-14 18:11:40.773146+00
\.


--
-- Data for Name: tags; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tags (id, name, category) FROM stdin;
0572ca64-8244-4bf9-84d8-f15098359dd1	Machine Learning	SKILL
ae683b0d-2085-4fae-be2b-5eedf05d23f1	Data Engineering	SKILL
bd596e6c-7260-455e-8e7a-510d6b73c041	Bioinformatics	SKILL
5ed2ef63-d818-43f7-8eb3-f64974ad3049	Robotics	SKILL
c2643739-ff93-4e18-a7d4-839241ebf91d	Cryptography	SKILL
438b9ac3-9fce-49d9-9f24-d2b48c9a6567	Materials Science	SKILL
39872157-4711-49f5-9328-ec64657a76e3	Climate Modeling	SKILL
28abb28d-e9e1-4c1e-a98e-66097f5e1421	Statistics	SKILL
cab93e31-a514-4338-af7f-67d2a7fe346d	NLP	SKILL
3fa39aff-99ed-485a-9035-e2f267a1df67	Computer Vision	SKILL
141c53dc-fcfc-40c9-a565-7ca93b21238d	Renewable Energy	RESEARCH_INTEREST
122396e4-c9b5-45e2-981c-af1363fe81ab	Genomics	RESEARCH_INTEREST
e5f2830a-a04a-4e63-b130-c7a0fbab9bc9	Quantum Computing	RESEARCH_INTEREST
de675499-001c-415d-ada0-8758207acd5c	Public Health	RESEARCH_INTEREST
6e397eb7-5486-40d5-b2f3-d84bed970b70	Neuroscience	RESEARCH_INTEREST
79b05aba-331f-409d-8524-beba605d003b	Astrophysics	RESEARCH_INTEREST
8fda1271-2dbe-4f21-bfb8-c96ec304ddc5	Cybersecurity	RESEARCH_INTEREST
371585b4-03e1-42e5-af74-8475deba4af7	Sustainable Agriculture	RESEARCH_INTEREST
8c9a442a-f877-4ab9-83bc-63e1e5fc3c05	Urban Planning	RESEARCH_INTEREST
8b95dcd6-40ee-440d-b84c-5a8a82eddce0	Ethics in AI	RESEARCH_INTEREST
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, email, hashed_password, role, is_active, is_verified, created_at, updated_at) FROM stdin;
e31e92f6-b5cd-4f32-89b0-f7e0f60fce6c	georgetracy@example.org	$2b$12$Yill6AdKzyJL1bZz24j.f.I0CZZd35vLb0zMEjxEjGZ5fqqgNSIvC	RESEARCHER	t	t	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
98b249da-4683-49ae-9816-219d5e88bc28	wrightjames@example.com	$2b$12$FjT.RLbNCoH8csd4.kCXhef73Wu2yS6hOkAYFsYsTD16a7BvAWpQS	RESEARCHER	t	t	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
8c111f53-82bc-4a04-9266-43038fa783a1	yuchristopher@example.org	$2b$12$QFHxXKnshiCes3hqHmZbGe3vmmj8LSyIPkp3mEB5u1jxyjLuH4sry	RESEARCHER	t	t	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
89502bcf-b017-4a0e-973b-6b2de3645509	mcmillandennis@example.org	$2b$12$hHmrOTSsv4sy3BL1u4wbhuJ53uJjB6a/nv/5p444vQT4EDlAuh9i.	RESEARCHER	t	t	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
8be42812-a925-40d3-a126-67dd60185abf	gomezanita@example.com	$2b$12$ZCYWFnqrjnyu4lrCpS6U/uRCgZPKxV0nDpg6RVIFL2ZpSvE8FkhNS	RESEARCHER	t	t	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
690410a3-7272-493b-a4e6-5453d9be8f66	samuel81@example.com	$2b$12$wURxYOanxmBcywe9u3XsbOFd7dECfFWCjPfmkQZfjy/4ZTT4Oh9Hm	RESEARCHER	t	t	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
8a2d6529-7abd-4364-9540-11912547f543	sanchezthomas@example.org	$2b$12$59eN0RtVGfgsOlSQfhesq.S/7CYnKMld0FWX3v4jTxMlZWFlYzaKm	RESEARCHER	t	t	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
4eff9dc0-b6e7-492d-bee1-3186ca4a3f4e	perrymark@example.com	$2b$12$3pumrbuAEhVRWVKOd63SPOA2slWIpkpwGE8iDRjSd3ZzKy6rKc1a6	RESEARCHER	t	t	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
11b7b056-32a9-4824-98c1-1d5b0e8183fa	debraharrington@example.net	$2b$12$NGys6Oq46VbUwlfWTqhhCuoj/aGAG.5pMVK5EewJ7zXlHEfR18OsG	RESEARCHER	t	t	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
66382120-b3bb-4575-bddd-077dfbf62091	dsanchez@example.net	$2b$12$3SFg8PDHAGihwXk20lpGGe.FG./ByLygHfsWOD9LSKtEVBzUOk7Eq	RESEARCHER	t	t	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
41cc97db-e8da-40fc-b33f-11e77be6680f	joshuamccann@example.net	$2b$12$O0wABt8LIYV7g/9t8hpbj.IDj/x3YS7uJqLjRgmqsEIrvapjt3hVW	RESEARCHER	t	t	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
7428238c-3b9f-4cb0-b60a-347c90c4763c	keithcampbell@example.com	$2b$12$/6oKc9i5lCCQFrWDroJl4u3x1w5JlfmlpEOGR9T2uFl19NkZBw38e	RESEARCHER	t	t	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
cc3f4dc2-76d5-4ce7-bda2-f35f46bdde04	howard96@example.net	$2b$12$KZPM7IhvkaS4h9PjQ9dsHejh7vlJquew4sRI8kAhHt/AAybuL5fg.	RESEARCHER	t	t	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
c772dbcb-9e87-42cf-867e-80b088df835a	murraydavid@example.org	$2b$12$OhOXXqun6vJd7K5AuY1TieC3YQOkh.vRetqQwF6E14VWG4eKUWpBK	RESEARCHER	t	t	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
5b33d6ea-5ab8-4dda-87bf-524ffb156597	molly71@example.net	$2b$12$mCDS/B2F3l6tvqfXGOgNm.kTInG2POXav3PxWMuyMmjhPyvy7B68W	RESEARCHER	t	t	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
3c348e00-1b8b-421a-a37e-4b0ac3eb5e91	charleslandry@example.net	$2b$12$ayBIvQ2Y5d30jSz0gpxdCuQIpYrXKGvaTtrSSz0avsE3mIvqkgk/a	RESEARCHER	t	t	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
7ba8716a-9273-4b37-be16-704d70f54b58	julie51@example.com	$2b$12$j/6BA0vZoklFRSq9oLCgIOxkb5S6mSvEWrsteTwg91G7snuR1YweW	INSTITUTION_ADMIN	t	t	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
c5903f6d-079a-4f17-b8d5-7fbbb07c5508	antonio53@example.com	$2b$12$1qP.tMK0Np2DRRSgMD2/oO3F4h2gkGOk8ummmHmXTt4xw1y3qNf1G	REVIEWER	t	t	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
5acecdbb-611f-4272-afe1-98665f118aba	stephen00@example.com	$2b$12$JAXd017mkETfj4kux7D3/.ZjcF1w6h4yAUPNCqSVPiIQuc65jhtaK	SYSTEM_ADMIN	t	t	2026-08-14 18:11:01.310566+00	2026-08-14 18:11:01.310566+00
3ab71c94-2c85-4781-b595-5fbd17b5db4d	admin@researchsphere.dev	$2b$12$MCB1Xw/Sdw8BzsMWUh45pOvpGcgQAjm6371P3yLEu6uv1zcYwwdXy	SYSTEM_ADMIN	t	t	2026-08-14 18:11:39.94785+00	2026-08-14 18:11:39.94785+00
262f7f28-8c4e-4641-9858-1f0a3c8905a7	institution.admin@researchsphere.dev	$2b$12$Hxg2O2ER/TNvRGHsJ.COxuFMHnJ9VU3aQXAS.rgI8XTgLWoxruZAe	INSTITUTION_ADMIN	t	t	2026-08-14 18:11:40.242449+00	2026-08-14 18:11:40.242449+00
08453c67-f6d7-4c3e-8412-3db6b4cf3b72	reviewer@researchsphere.dev	$2b$12$WBS3fzqyg1daNKwYjutrMe9zKqG3.EG54T2.zTS7McL.6C00.72Di	REVIEWER	t	t	2026-08-14 18:11:40.504325+00	2026-08-14 18:11:40.504325+00
3b277ce0-d701-462f-bfc0-67624b0c5087	researcher@researchsphere.dev	$2b$12$F68sY.ndaKqZ54166ssRre.y.y7fhLLZZR88bLokDQg1RtFtaDHFS	RESEARCHER	t	t	2026-08-14 18:11:40.773146+00	2026-08-14 18:11:40.773146+00
\.


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: citations citations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.citations
    ADD CONSTRAINT citations_pkey PRIMARY KEY (id);


--
-- Name: collaborations collaborations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.collaborations
    ADD CONSTRAINT collaborations_pkey PRIMARY KEY (id);


--
-- Name: conference_participations conference_participations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conference_participations
    ADD CONSTRAINT conference_participations_pkey PRIMARY KEY (id);


--
-- Name: conferences conferences_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conferences
    ADD CONSTRAINT conferences_pkey PRIMARY KEY (id);


--
-- Name: institutions institutions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.institutions
    ADD CONSTRAINT institutions_pkey PRIMARY KEY (id);


--
-- Name: project_members project_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_pkey PRIMARY KEY (project_id, researcher_id);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: publication_authors publication_authors_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publication_authors
    ADD CONSTRAINT publication_authors_pkey PRIMARY KEY (publication_id, researcher_id);


--
-- Name: publications publications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publications
    ADD CONSTRAINT publications_pkey PRIMARY KEY (id);


--
-- Name: researcher_tags researcher_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.researcher_tags
    ADD CONSTRAINT researcher_tags_pkey PRIMARY KEY (researcher_id, tag_id);


--
-- Name: researchers researchers_orcid_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.researchers
    ADD CONSTRAINT researchers_orcid_id_key UNIQUE (orcid_id);


--
-- Name: researchers researchers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.researchers
    ADD CONSTRAINT researchers_pkey PRIMARY KEY (id);


--
-- Name: researchers researchers_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.researchers
    ADD CONSTRAINT researchers_user_id_key UNIQUE (user_id);


--
-- Name: tags tags_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT tags_pkey PRIMARY KEY (id);


--
-- Name: tags uq_tag_name_category; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT uq_tag_name_category UNIQUE (name, category);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_conferences_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_conferences_name ON public.conferences USING btree (name);


--
-- Name: ix_institutions_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_institutions_name ON public.institutions USING btree (name);


--
-- Name: ix_publications_doi; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_publications_doi ON public.publications USING btree (doi);


--
-- Name: ix_publications_title; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_publications_title ON public.publications USING btree (title);


--
-- Name: ix_tags_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_tags_name ON public.tags USING btree (name);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: citations citations_cited_publication_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.citations
    ADD CONSTRAINT citations_cited_publication_id_fkey FOREIGN KEY (cited_publication_id) REFERENCES public.publications(id) ON DELETE CASCADE;


--
-- Name: citations citations_citing_publication_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.citations
    ADD CONSTRAINT citations_citing_publication_id_fkey FOREIGN KEY (citing_publication_id) REFERENCES public.publications(id) ON DELETE CASCADE;


--
-- Name: collaborations collaborations_institution_a_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.collaborations
    ADD CONSTRAINT collaborations_institution_a_id_fkey FOREIGN KEY (institution_a_id) REFERENCES public.institutions(id) ON DELETE CASCADE;


--
-- Name: collaborations collaborations_institution_b_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.collaborations
    ADD CONSTRAINT collaborations_institution_b_id_fkey FOREIGN KEY (institution_b_id) REFERENCES public.institutions(id) ON DELETE CASCADE;


--
-- Name: collaborations collaborations_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.collaborations
    ADD CONSTRAINT collaborations_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: conference_participations conference_participations_conference_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conference_participations
    ADD CONSTRAINT conference_participations_conference_id_fkey FOREIGN KEY (conference_id) REFERENCES public.conferences(id) ON DELETE CASCADE;


--
-- Name: conference_participations conference_participations_publication_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conference_participations
    ADD CONSTRAINT conference_participations_publication_id_fkey FOREIGN KEY (publication_id) REFERENCES public.publications(id) ON DELETE SET NULL;


--
-- Name: conference_participations conference_participations_researcher_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conference_participations
    ADD CONSTRAINT conference_participations_researcher_id_fkey FOREIGN KEY (researcher_id) REFERENCES public.researchers(id) ON DELETE CASCADE;


--
-- Name: project_members project_members_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_members project_members_researcher_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_researcher_id_fkey FOREIGN KEY (researcher_id) REFERENCES public.researchers(id) ON DELETE CASCADE;


--
-- Name: projects projects_lead_institution_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_lead_institution_id_fkey FOREIGN KEY (lead_institution_id) REFERENCES public.institutions(id) ON DELETE SET NULL;


--
-- Name: projects projects_lead_researcher_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_lead_researcher_id_fkey FOREIGN KEY (lead_researcher_id) REFERENCES public.researchers(id) ON DELETE SET NULL;


--
-- Name: publication_authors publication_authors_publication_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publication_authors
    ADD CONSTRAINT publication_authors_publication_id_fkey FOREIGN KEY (publication_id) REFERENCES public.publications(id) ON DELETE CASCADE;


--
-- Name: publication_authors publication_authors_researcher_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publication_authors
    ADD CONSTRAINT publication_authors_researcher_id_fkey FOREIGN KEY (researcher_id) REFERENCES public.researchers(id) ON DELETE CASCADE;


--
-- Name: publications publications_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publications
    ADD CONSTRAINT publications_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: researcher_tags researcher_tags_researcher_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.researcher_tags
    ADD CONSTRAINT researcher_tags_researcher_id_fkey FOREIGN KEY (researcher_id) REFERENCES public.researchers(id) ON DELETE CASCADE;


--
-- Name: researcher_tags researcher_tags_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.researcher_tags
    ADD CONSTRAINT researcher_tags_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tags(id) ON DELETE CASCADE;


--
-- Name: researchers researchers_institution_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.researchers
    ADD CONSTRAINT researchers_institution_id_fkey FOREIGN KEY (institution_id) REFERENCES public.institutions(id) ON DELETE SET NULL;


--
-- Name: researchers researchers_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.researchers
    ADD CONSTRAINT researchers_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict YwIbxMifGzmh2bNchKudf8UJQ0mb7Y9k6ts1jNmReDBInR4II41f6dmJQV7KBlG

