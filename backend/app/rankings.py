import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import numpy as np
from db_schema import (
    DeepResearchUserResponse,
    AnswerSpanVote,
    IntermediateStepVote,
    DeepresearchRankings,
    DeepResearchAgent,
)
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import and_
from scipy.special import expit
from scipy.optimize import minimize
import math

load_dotenv()  # Load from .env file and environment variables


DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_ENDPOINT = os.getenv("DB_ENDPOINT")
DB_PORT = 5432
DB_NAME = os.getenv("DB_NAME")

DB_URI = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_ENDPOINT}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DB_URI, echo=False)
Session = sessionmaker(bind=engine)
session = Session()

# We use the field agent_id to identify all the agents


class rankings:
    def __init__(self, agent_id, rating=0):
        self.SYSTEMID = agent_id
        self.SYSTEMNAME = "None"
        self.VOTES = 0
        self.RANK = 0
        self.ARENASCORE = rating
        self.STEPUPVOTE_RATE = 0
        self.TEXTUPVOTE_RATE = 0


def return_bt_dataframe():
    rows = session.query(
        DeepResearchUserResponse.agentid_a,
        DeepResearchUserResponse.agentid_b,
        DeepResearchUserResponse.userresponse,
    ).all()
    updated_rows = []
    for row in rows:
        if row[2] == "choice1":
            new_tuple = (row[0], row[1], "agent_a")
            updated_rows.append(new_tuple)
        elif row[2] == "choice2":
            new_tuple = (row[0], row[1], "agent_b")
            updated_rows.append(new_tuple)
    df = pd.DataFrame(updated_rows, columns=["agent_a", "agent_b", "winner"])
    return df


def get_matchups_agents(df):
    n_rows = len(df)
    agent_indices, agents = pd.factorize(pd.concat([df["agent_a"], df["agent_b"]]))
    matchups = np.column_stack([agent_indices[:n_rows], agent_indices[n_rows:]])
    return matchups, agents.to_list()


def preprocess_for_bt(df):
    """in BT we only need the unique (matchup,outcome) sets along with the weights of how often they occur"""
    n_rows = len(df)
    # the 3 columns of schedule represent: agent_a id, agent_b id, outcome_id
    schedule = np.full((n_rows, 3), fill_value=1, dtype=np.int32)
    # set the two agent cols by mapping the agent names to their int ids
    schedule[:, [0, 1]], agents = get_matchups_agents(df)
    # map outcomes to integers (must be same dtype as agent ids so it can be in the same array)
    # agent_a win -> 2, tie -> 1 (prefilled by default), agent_b win -> 0
    schedule[df["winner"] == "agent_a", 2] = 2
    schedule[df["winner"] == "agent_b", 2] = 0
    # count the number of occurances of each observed result
    matchups_outcomes, weights = np.unique(schedule, return_counts=True, axis=0)
    matchups = matchups_outcomes[:, [0, 1]]
    # map 2 -> 1.0, 1 -> 0.5, 0 -> 0.0 which will be used as labels during optimization
    outcomes = matchups_outcomes[:, 2].astype(np.float64) / 2.0
    weights = weights.astype(np.float64)
    # each possible result is weighted according to number of times it occured in the dataset
    return matchups, outcomes, agents, weights


def bt_loss_and_grad(ratings, matchups, outcomes, weights, alpha=1.0):
    matchup_ratings = ratings[matchups]
    logits = alpha * (matchup_ratings[:, 0] - matchup_ratings[:, 1])
    probs = expit(logits)
    # this form naturally counts a draw as half a win and half a loss
    loss = -(
        (np.log(probs) * outcomes + np.log(1.0 - probs) * (1.0 - outcomes)) * weights
    ).sum()
    matchups_grads = -alpha * (outcomes - probs) * weights
    agent_grad = np.zeros_like(ratings)
    # aggregate gradients at the agent level using the indices in matchups
    np.add.at(
        agent_grad,
        matchups[:, [0, 1]],
        matchups_grads[:, None] * np.array([1.0, -1.0], dtype=np.float64),
    )
    return loss, agent_grad


def fit_bt(matchups, outcomes, weights, n_agents, alpha, tol=1e-6):
    initial_ratings = np.zeros(n_agents, dtype=np.float64)
    result = minimize(
        fun=bt_loss_and_grad,
        x0=initial_ratings,
        args=(matchups, outcomes, weights, alpha),
        jac=True,
        method="L-BFGS-B",
        options={"disp": False, "maxiter": 100, "gtol": tol},
    )
    return result["x"]


def scale_and_offset(
    ratings,
    agents,
    scale=400,
    init_rating=1000,
    baseline_agent="baseline",
    baseline_rating=1114,
):
    """convert ratings from the natural scale to the Elo rating scale with an anchored baseline"""
    scaled_ratings = (ratings * scale) + init_rating
    if baseline_agent in agents:
        baseline_idx = agents.index(baseline_agent)
        scaled_ratings += baseline_rating - scaled_ratings[..., [baseline_idx]]
    return scaled_ratings


def compute_bt(df, base=10.0, scale=400.0, init_rating=1000, tol=1e-6):
    matchups, outcomes, agents, weights = preprocess_for_bt(df)
    ratings = fit_bt(matchups, outcomes, weights, len(agents), math.log(base), tol)
    scaled_ratings = scale_and_offset(ratings, agents, scale, init_rating=init_rating)
    return pd.Series(scaled_ratings, index=agents).sort_values(ascending=False)


def compute_Answering_Span_Upvote_rate(agent_id):
    count_ans = (
        session.query(AnswerSpanVote.agent_id, AnswerSpanVote.vote)
        .filter(AnswerSpanVote.agent_id == agent_id)
        .all()
    )
    rows_up = (
        session.query(AnswerSpanVote.agent_id, AnswerSpanVote.vote)
        .filter(and_(AnswerSpanVote.agent_id == agent_id, AnswerSpanVote.vote == "up"))
        .all()
    )

    rows_down = (
        session.query(AnswerSpanVote.agent_id, AnswerSpanVote.vote)
        .filter(
            and_(AnswerSpanVote.agent_id == agent_id, AnswerSpanVote.vote == "down")
        )
        .all()
    )

    assert len(rows_up) + len(rows_down) == len(count_ans)
    return round(len(rows_up) / len(count_ans), 2)


def compute_Step_Upvote_Rate(agent_id):
    count_ans = (
        session.query(IntermediateStepVote.agent_id, IntermediateStepVote.vote)
        .filter(IntermediateStepVote.agent_id == agent_id)
        .all()
    )
    rows_up = (
        session.query(IntermediateStepVote.agent_id, IntermediateStepVote.vote)
        .filter(
            and_(
                IntermediateStepVote.agent_id == agent_id,
                IntermediateStepVote.vote == "up",
            )
        )
        .all()
    )

    rows_down = (
        session.query(IntermediateStepVote.agent_id, IntermediateStepVote.vote)
        .filter(
            and_(
                IntermediateStepVote.agent_id == agent_id,
                IntermediateStepVote.vote == "down",
            )
        )
        .all()
    )

    assert len(rows_up) + len(rows_down) == len(count_ans)
    return round(len(rows_up) / len(count_ans), 2)


def calculate_total_votes(agent_id):
    total_votes = 0
    rows1 = (
        session.query(
            DeepResearchUserResponse.agentid_a,
            DeepResearchUserResponse.agentid_b,
            DeepResearchUserResponse.userresponse,
        )
        .filter(
            and_(
                DeepResearchUserResponse.agentid_a == agent_id,
                DeepResearchUserResponse.userresponse == "choice1",
            )
        )
        .all()
    )
    total_votes += len(rows1)
    rows2 = (
        session.query(
            DeepResearchUserResponse.agentid_a,
            DeepResearchUserResponse.agentid_b,
            DeepResearchUserResponse.userresponse,
        )
        .filter(
            and_(
                DeepResearchUserResponse.agentid_b == agent_id,
                DeepResearchUserResponse.userresponse == "choice2",
            )
        )
        .all()
    )
    total_votes += len(rows2)
    return total_votes


def return_system_name(agent_id):
    rows = (
        session.query(DeepResearchAgent.agent_name)
        .filter(DeepResearchAgent.agent_id == agent_id)
        .all()
    )
    assert len(rows) == 1
    return rows[0][0]


def insert_into_rankings(sorted_rankings_object_array):
    for obj in sorted_rankings_object_array:
        rows = (
            session.query(DeepresearchRankings.SYSTEMID)
            .filter(DeepresearchRankings.SYSTEMID == obj.SYSTEMID)
            .all()
        )
        if len(rows) == 0:
            new_record = DeepresearchRankings(
                SYSTEMID=obj.SYSTEMID,
                SYSTEMNAME=obj.SYSTEMNAME,
                VOTES=obj.VOTES,
                RANK=obj.RANK,
                ARENASCORE=obj.ARENASCORE,
                STEPUPVOTE_RATE=obj.STEPUPVOTE_RATE,
                TEXTUPVOTE_RATE=obj.TEXTUPVOTE_RATE,
                ISLATEST=True,
            )
            session.add(new_record)
            session.commit()
        # change the status of ISLATEST to false and enter a new ranking
        elif len(rows) >= 1:
            session.query(DeepresearchRankings).filter(
                DeepresearchRankings.SYSTEMID == obj.SYSTEMID,
                DeepresearchRankings.ISLATEST == True,
            ).update({"ISLATEST": False})
            new_record = DeepresearchRankings(
                SYSTEMID=obj.SYSTEMID,
                SYSTEMNAME=obj.SYSTEMNAME,
                VOTES=obj.VOTES,
                RANK=obj.RANK,
                ARENASCORE=obj.ARENASCORE,
                STEPUPVOTE_RATE=obj.STEPUPVOTE_RATE,
                TEXTUPVOTE_RATE=obj.TEXTUPVOTE_RATE,
                ISLATEST=True,
            )
            session.add(new_record)
            session.commit()


def main():
    rating_array = []

    df = return_bt_dataframe()
    bt_scores = compute_bt(df)
    for agent, rating in bt_scores.items():
        rating_array.append(rankings(agent, round(rating, 0)))

    for rating in rating_array:
        rating.SYSTEMNAME = return_system_name(rating.SYSTEMID)
        rating.TEXTUPVOTE_RATE = compute_Answering_Span_Upvote_rate(rating.SYSTEMID)
        rating.STEPUPVOTE_RATE = compute_Step_Upvote_Rate(rating.SYSTEMID)
        rating.VOTES = calculate_total_votes(rating.SYSTEMID)
    sorted_rankings = sorted(rating_array, key=lambda x: x.ARENASCORE, reverse=True)
    for i in range(len(sorted_rankings)):
        sorted_rankings[i].RANK = i + 1
    insert_into_rankings(sorted_rankings)
    for agent in rating_array:
        print(agent.SYSTEMNAME)
        print(agent.VOTES)
        print(agent.RANK)
        print(agent.ARENASCORE)
        print(agent.STEPUPVOTE_RATE)
        print(agent.TEXTUPVOTE_RATE)
        print("------------------")


if __name__ == "__main__":
    main()
